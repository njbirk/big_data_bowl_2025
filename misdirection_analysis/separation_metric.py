from . import data
import os
import pandas as pd
import tqdm
import numpy as np


SEPARATION_COLUMN_NAME = "separation"

# in yards per frame
PASS_SPEED = 2

# assume qb drops back 5 yards before pass
QB_DROP_BACK = 5


def _compute_separation_metric(
    receiver: pd.DataFrame, defender: pd.DataFrame
) -> np.ndarray:
    # compute theoretical pass time
    pass_distance = np.sqrt(
        receiver["x"].values ** 2 + (receiver["y"].values - QB_DROP_BACK) ** 2
    )
    t_frame = pass_distance / PASS_SPEED
    t_sec = t_frame / 10

    # exptrapolate x and y
    x_extrap = (
        receiver["x"].values
        + receiver["v_x"].values * t_sec
        + 0.5 * receiver["a_x"].values * t_sec**2
    )
    y_extrap = (
        receiver["y"].values
        + receiver["v_y"].values * t_sec
        + 0.5 * receiver["a_y"].values * t_sec**2
    )

    # vector from defender to receivers extrapolation
    dir_x = x_extrap - defender["x"].values
    dir_y = y_extrap - defender["y"].values
    magnitude = np.sqrt(dir_x**2 + dir_y**2)
    ux = dir_x / magnitude
    uy = dir_y / magnitude

    # compute the relative velocity
    rvelo_x = ux * defender["v_x"].values
    rvelo_y = uy * defender["v_y"].values
    rvelo = rvelo_x + rvelo_y

    # devide by the distance squared
    separation = rvelo / (
        (receiver["x"].values - defender["x"].values) ** 2
        + (receiver["y"].values - defender["y"].values) ** 2
    )

    return separation


def append_separation_metric(force_calc: bool = False, sepbase_id: str = "main"):
    """
    Calculate separation and append the separation column to the adjusted tracking data.

    Pass `force_calc = True` to force the separation column to be recalculated even if it exists.
    """
    # load in the data
    games = pd.read_csv(os.path.join(data.DATA_DIR, "games.csv"))
    plays = pd.read_csv(os.path.join(data.DATA_DIR, "plays.csv"))
    player_play = pd.read_csv(os.path.join(data.DATA_DIR, "player_play.csv"))
    players = pd.read_csv(os.path.join(data.DATA_DIR, "players.csv"))

    # get position groups for player plays
    players = data.get_postion_groups(players)
    player_play = pd.merge(player_play, players[["nflId", "position_group"]])

    # iterate through each adjusted tracking game file
    all_gids = games["gameId"].unique()
    with tqdm.tqdm(
        total=len(all_gids), desc="Calculating separation tracking column"
    ) as pbar:
        for gid in all_gids:
            tracking = data.load_tracking_adjusted(gid)

            # if the separation column already exists and we do not force_calc is False, there is nothing more to be done - return
            if SEPARATION_COLUMN_NAME in tracking.columns and not force_calc:
                pbar.n = len(all_gids)
                pbar.last_print_n = len(all_gids)
                pbar.update(0)
                return

            # get plays for this game
            plays_game_mask = plays["gameId"] == gid
            plays_game = plays[plays_game_mask]

            # get only player play data for this game
            player_play_game_mask = player_play["gameId"] == gid
            player_play_game = player_play[player_play_game_mask]

            # iterate over each play
            all_pids = tracking["playId"].unique()
            for pid in all_pids:
                # get this play
                play = plays_game[plays_game["playId"] == pid].squeeze()

                # if not a passing play, continue to next play
                if not play["isDropback"]:
                    continue

                # get frames for this play
                tracking_play_mask = tracking["playId"] == pid
                tracking_play: pd.DataFrame = tracking[tracking_play_mask]

                # get player plays for this play
                player_play_play_mask = player_play_game["playId"] == pid
                player_play_play: pd.DataFrame = player_play_game[player_play_play_mask]

                # get potential recievers for this play (running_back, tight_end, receiver)
                receiver_mask = player_play_play["position_group"].isin(
                    ["running_back", "tight_end", "receiver"]
                )
                receiverIds = player_play_play.loc[receiver_mask, "nflId"].values

                # get potential defenders for this play (saftey, cornerback, linebacker)
                defender_mask = player_play_play["position_group"].isin(
                    ["safety", "cornerback", "linebacker"]
                )
                defenderIds = player_play_play.loc[defender_mask, "nflId"].values

                # get frames for relevant players
                players_mask = tracking_play["nflId"].isin(
                    np.concatenate((receiverIds, defenderIds))
                )
                tracking_relevant = tracking_play[players_mask]

                # get each receivers frames
                receiver_frames = []
                for receiver in receiverIds:
                    tracking_receiver = tracking_relevant[
                        tracking_relevant["nflId"] == receiver
                    ]
                    receiver_frames.append(tracking_receiver)

                # get the defenders frames
                defender_frames = []
                for defender in defenderIds:
                    tracking_defender = tracking_relevant[
                        tracking_relevant["nflId"] == defender
                    ]
                    defender_frames.append(tracking_defender)

                # create the frame dictionaries
                receivers_dict = dict(zip(receiverIds, receiver_frames))
                defenders_dict = dict(zip(defenderIds, defender_frames))

                # calculate the separation for each receiver-defender combo
                for receiverId, receiver in receivers_dict.items():
                    separation_array = None
                    for defender in defenders_dict.values():
                        this_separation_array = _compute_separation_metric(
                            receiver, defender
                        )

                        if isinstance(separation_array, np.ndarray):
                            separation_array += this_separation_array
                        else:
                            separation_array = this_separation_array

                    # append the separation to the tracking data
                    tracking_player_mask = tracking["nflId"] == receiverId
                    tracking.loc[
                        tracking_play_mask & tracking_player_mask,
                        SEPARATION_COLUMN_NAME,
                    ] = separation_array

            # update the progress bar
            pbar.update(1)

            # write the new adjusted tracking data with the separation column
            tracking.to_parquet(data.tracking_adjusted_path(gid))
