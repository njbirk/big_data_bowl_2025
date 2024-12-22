import pandas as pd
import os
import tqdm
import numpy as np


# ================ #
# Raw Data Loading #
# ================ #

#   | Save the tracking data in parquet format for
#   | ease of use in the directory "data/parqs/"
#   | -- Ensure the directory exists on first run --
#   | use load_tracking() to get tracking data by gid and pid


DATA_DIR = os.path.join(os.path.dirname(__file__), "../data/")
_PARQ_DIR = os.path.join(os.path.dirname(__file__), "../data/parqs/")


def tracking_raw_path(gid: int) -> str:
    return os.path.join(_PARQ_DIR, f"tracking-{gid}.parq")


def _create_tracking_week_raw(week: int):
    week_df = pd.read_csv(os.path.join(DATA_DIR, f"tracking_week_{week}.csv"))
    gids = week_df["gameId"].unique()
    for gid in gids:
        game_df: pd.DataFrame = week_df[week_df["gameId"] == gid]
        path = tracking_raw_path(gid)
        game_df.to_parquet(path)


def _create_tracking_raw():
    for week in tqdm.tqdm(range(1, 10), desc="Creating parquet game files"):
        _create_tracking_week_raw(week)


def load_tracking_raw(gid: int) -> pd.DataFrame:
    """
    Load tracking data for the game ID given. Stores data in parquet form in the parqs directory. Much faster IO than CSV storage.
    """
    path = tracking_raw_path(gid)
    if not os.path.exists(path):
        _create_tracking_raw()
    df = pd.read_parquet(path)
    return df


# ============= #
# Data Cleaning #
# ============= #

#   | Peform coord flipping/zeroing and position grouping


def get_postion_groups(players: pd.DataFrame) -> pd.DataFrame:
    """
    Assigns position groups to all players to make it easier to group them later
    """

    positions = {
        "oline": ["T", "G", "C"],
        "tight_end": ["TE"],
        "receiver": ["WR"],
        "running_back": ["RB", "FB"],
        "quarterback": ["QB"],
        "dline": ["DT", "DE", "NT"],
        "linebacker": ["LB", "OLB", "ILB", "MLB"],
        "cornerback": ["CB"],
        "safety": ["SS", "FS"],
    }

    players["position_group"] = players["position"].apply(
        lambda x: next((k for k, v in positions.items() if x in v), None)
    )

    return players


# note: the original coordinates are flipped to (x, y) rather than (y, x)
# ====================================================
#           Football's y = 0       Player Orientation
#                ^
#                |                          0
#            |---|---|                      ^
#    (-,+)   |Defense|    (+,+)       270 <-|-> 90
#            |---|---|                      V
#                |                         180
#                |
# <---------Football---------> Line of Scrimmage
#                |
#            |---|---|
#    (-,-)   |Offense|    (+,-)
#            |---|---|
#                |
#                V
# ====================================================


def _clean_coords(tracking: pd.DataFrame, plays: pd.DataFrame) -> pd.DataFrame:
    """
    Adjusts the coordinates of the players to be relative to the line of scrimmage
    """
    # adjust x relative to line of scrimmage
    tracking = pd.merge(
        tracking,
        plays[["gameId", "playId", "absoluteYardlineNumber"]],
        on=["gameId", "playId"],
    )
    tracking["x"] -= tracking["absoluteYardlineNumber"]
    tracking.drop(columns=["absoluteYardlineNumber"])

    # adjust y relative to footballs position
    football_mask = (tracking["displayName"] == "football") & (
        (tracking["event"] == "ball_snap") | (tracking["event"] == "snap_direct")
    )
    tracking = pd.merge(
        tracking,
        tracking.loc[football_mask, ["playId", "y"]].rename(
            {"y": "football_y"}, axis="columns"
        ),
        on="playId",
    )
    tracking["y"] = tracking["football_y"] - tracking["y"]
    tracking.drop(columns=["football_y"])

    # correct player orientation and direction
    tracking["o"] = (tracking["o"] + 270) % 360
    tracking["dir"] = (tracking["dir"] + 270) % 360

    # flip the x and y coordinate and adjust orientation if the play direction is left
    direction_mask = tracking["playDirection"] == "left"
    tracking.loc[direction_mask, "x"] *= -1
    tracking.loc[direction_mask, "y"] *= -1
    tracking.loc[direction_mask, "o"] = (tracking.loc[direction_mask, "o"] + 180) % 360

    # flip coordinates to (x, y) instead of (y, x)
    tracking = tracking.rename({"x": "y", "y": "x"}, axis="columns")

    return tracking


# ================== #
# Vector Calculation #
# ================== #


def _compute_orien_vec(tracking: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the orientation vector for a player play
    """
    tracking["o_x"] = np.sin(np.radians(tracking["o"]))
    tracking["o_y"] = np.cos(np.radians(tracking["o"]))
    return tracking


def _compute_velo_vec(tracking: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the velocity vector for a player play
    """
    tracking["d_x"] = np.sin(np.radians(tracking["dir"]))
    tracking["d_y"] = np.cos(np.radians(tracking["dir"]))
    tracking["v_x"] = tracking["d_x"] * tracking["s"]
    tracking["v_y"] = tracking["d_y"] * tracking["s"]
    tracking.drop(columns=["d_x", "d_y"])
    return tracking


def _compute_accel_vec(tracking: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the acceleration vector for a player play
    """
    # compute the acceleration vector
    tracking["a_x"] = (tracking["v_x"].shift(-1) - tracking["v_x"].shift(1)) / 0.2
    tracking["a_y"] = (tracking["v_y"].shift(-1) - tracking["v_y"].shift(1)) / 0.2

    # adjust for edge case frames (ID = 1 or 200)
    id1 = tracking["frameId"] == 1
    tracking.loc[id1, "a_x"] = tracking["a_x"].shift(-1)
    tracking.loc[id1, "a_y"] = tracking["a_y"].shift(-1)
    id200 = tracking["frameId"] == 200
    tracking.loc[id200, "a_x"] = tracking["a_x"].shift(1)
    tracking.loc[id200, "a_y"] = tracking["a_y"].shift(1)

    return tracking


def _compute_vectors(tracking: pd.DataFrame) -> pd.DataFrame:
    tracking = _compute_orien_vec(tracking)
    tracking = _compute_velo_vec(tracking)
    tracking = _compute_accel_vec(tracking)
    return tracking


# ===================== #
# Adjusted Data Loading #
# ===================== #


def tracking_adjusted_path(gid: int) -> str:
    return os.path.join(_PARQ_DIR, f"tracking-adjusted-{gid}.parq")


def _create_tracking_adjusted_game(gid: int, plays: pd.DataFrame):
    # load in the tracking data
    tracking_path = tracking_raw_path(gid)
    if not os.path.exists(tracking_path):
        _create_tracking_raw()
    tracking = pd.read_parquet(tracking_path)

    # clean the coordinates
    tracking = _clean_coords(tracking, plays)

    # compute the vectors for every player for every play
    tracking = _compute_vectors(tracking)

    # drop unnecessary columns
    tracking.drop(columns=["o", "s", "a", "dir"])

    # write the adjusted tracking data
    adjusted_tracking_path = tracking_adjusted_path(gid)
    tracking.to_parquet(adjusted_tracking_path)


def _create_tracking_adjusted():
    games = pd.read_csv(os.path.join(DATA_DIR, "games.csv"))
    plays = pd.read_csv(os.path.join(DATA_DIR, "plays.csv"))
    all_gid = games["gameId"].unique()
    for gid in tqdm.tqdm(all_gid, desc="Creating adjusted parquet game files"):
        _create_tracking_adjusted_game(gid, plays)


def load_tracking_adjusted(gid: int) -> pd.DataFrame:
    """
    Load tracking data for the game ID given. Stores data in parquet form in the parqs directory. Much faster IO than CSV storage.
    """
    path = tracking_adjusted_path(gid)
    if not os.path.exists(path):
        _create_tracking_adjusted()
    df = pd.read_parquet(path)
    return df
