import pandas
import os
import tqdm


_DATA_DIR = os.path.join(os.path.dirname(__file__), "parqs/")


def _create_tracking_week(week: int):
    week_df = pandas.read_csv(f"data/tracking_week_{week}.csv")
    gids = week_df["gameId"].unique()
    for gid in gids:
        game_df = week_df[week_df["gameId"] == gid]
        path = os.path.join(_DATA_DIR, f"tracking-{gid}.parq")
        game_df.to_parquet(path)


def _create_tracking():
    for week in tqdm.tqdm(range(1, 10), desc="Creating parquet game files"):
        _create_tracking_week(week)


def load_tracking(gid: int) -> pandas.DataFrame:
    """
    Load tracking data for the game ID given. Stores data in parquet form in the parqs directory. Much faster IO than CSV storage.
    """
    path = os.path.join(_DATA_DIR, f"tracking-{gid}.parq")
    if not os.path.exists(path):
        _create_tracking()
    return pandas.read_parquet(path)
