from . import data
import pandas as pd
import os
import tqdm
from .motion_detection import MOTION_EVENT_COLUMN_NAME
import numpy as np
from . import data


CLASSIFICATION_COLUMN_NAME = "premotion_classification"


CROSSOVER_LEFT_JET = "crossover_left_jet"


def _crossover_left_jet(tracking: pd.DataFrame) -> bool:
    SPEED_THRESH = -2
    X_THRESH = 5

    initial_x = tracking["x"].iloc[0]
    final_x = tracking["x"].iloc[-1]
    final_v_x = tracking["v_x"].iloc[-1]

    if initial_x > 0 and final_x < X_THRESH and final_v_x < SPEED_THRESH:
        return True
    else:
        return False


CROSSOVER_RIGHT_JET = "crossover_right_jet"


def _crossover_right_jet(tracking: pd.DataFrame) -> bool:
    SPEED_THRESH = 2
    X_THRESH = -5

    initial_x = tracking["x"].iloc[0]
    final_x = tracking["x"].iloc[-1]
    final_v_x = tracking["v_x"].iloc[-1]

    if initial_x < 0 and final_x > X_THRESH and final_v_x > SPEED_THRESH:
        return True
    else:
        return False


CROSSOVER_LEFT_SET = "crossover_left_set"


def _crossover_left_set(tracking: pd.DataFrame) -> bool:
    X_THRESH = 2.5
    SPEED_THRESH = 2

    initial_x = tracking["x"].iloc[0]
    final_x = tracking["x"].iloc[-1]
    final_speed = tracking["s"].iloc[-1]

    if initial_x > X_THRESH and final_x < -X_THRESH and final_speed < SPEED_THRESH:
        return True
    else:
        return False


CROSSOVER_RIGHT_SET = "crossover_right_set"


def _crossover_right_set(tracking: pd.DataFrame) -> bool:
    X_THRESH = -2.5
    SPEED_THRESH = 2

    initial_x = tracking["x"].iloc[0]
    final_x = tracking["x"].iloc[-1]
    final_speed = tracking["s"].iloc[-1]

    if initial_x < X_THRESH and final_x > -X_THRESH and final_speed < SPEED_THRESH:
        return True
    else:
        return False


LEFT_SIDE_SHIFT_LEFT = "left_side_shift_left"


def _left_side_shift_left(tracking: pd.DataFrame) -> bool:
    SPEED_THRESH = 2

    initial_x = tracking["x"].iloc[0]
    final_x = tracking["x"].iloc[-1]
    final_speed = tracking["s"].iloc[-1]

    if (
        initial_x < 0
        and final_x < 0
        and final_x < initial_x
        and final_speed < SPEED_THRESH
    ):
        return True
    else:
        return False


LEFT_SIDE_SHIFT_RIGHT = "left_side_shift_right"


def _left_side_shift_right(tracking: pd.DataFrame) -> bool:
    SPEED_THRESH = 2

    initial_x = tracking["x"].iloc[0]
    final_x = tracking["x"].iloc[-1]
    final_speed = tracking["s"].iloc[-1]

    if (
        initial_x < 0
        and final_x < 0
        and final_x > initial_x
        and final_speed < SPEED_THRESH
    ):
        return True
    else:
        return False


RIGHT_SIDE_SHIFT_LEFT = "right_side_shift_left"


def _right_side_shift_left(tracking: pd.DataFrame) -> bool:
    SPEED_THRESH = 2

    initial_x = tracking["x"].iloc[0]
    final_x = tracking["x"].iloc[-1]
    final_speed = tracking["s"].iloc[-1]

    if (
        initial_x > 0
        and final_x > 0
        and final_x < initial_x
        and final_speed < SPEED_THRESH
    ):
        return True
    else:
        return False


RIGHT_SIDE_SHIFT_RIGHT = "right_side_shift_right"


def _right_side_shift_right(tracking: pd.DataFrame) -> bool:
    SPEED_THRESH = 2

    initial_x = tracking["x"].iloc[0]
    final_x = tracking["x"].iloc[-1]
    final_speed = tracking["s"].iloc[-1]

    if (
        initial_x > 0
        and final_x > 0
        and final_x > initial_x
        and final_speed < SPEED_THRESH
    ):
        return True
    else:
        return False


LEFT_SIDE_JET_LEFT = "left_side_jet_left"


def _left_side_jet_left(tracking: pd.DataFrame) -> bool:
    SPEED_THRESH = 2

    initial_x = tracking["x"].iloc[0]
    final_x = tracking["x"].iloc[-1]
    final_speed = tracking["s"].iloc[-1]

    if (
        initial_x < 0
        and final_x < 0
        and final_x < initial_x
        and final_speed > SPEED_THRESH
    ):
        return True
    else:
        return False


LEFT_SIDE_JET_RIGHT = "left_side_jet_right"


def _left_side_jet_right(tracking: pd.DataFrame) -> bool:
    SPEED_THRESH = 2
    X_THRESH = -5

    initial_x = tracking["x"].iloc[0]
    final_x = tracking["x"].iloc[-1]
    final_speed = tracking["s"].iloc[-1]

    if (
        initial_x < 0
        and final_x < X_THRESH
        and final_x > initial_x
        and final_speed > SPEED_THRESH
    ):
        return True
    else:
        return False


RIGHT_SIDE_JET_LEFT = "right_side_jet_left"


def _right_side_jet_left(tracking: pd.DataFrame) -> bool:
    SPEED_THRESH = 2
    X_THRESH = 5

    initial_x = tracking["x"].iloc[0]
    final_x = tracking["x"].iloc[-1]
    final_speed = tracking["s"].iloc[-1]

    if (
        initial_x > 0
        and final_x > X_THRESH
        and final_x < initial_x
        and final_speed > SPEED_THRESH
    ):
        return True
    else:
        return False


RIGHT_SIDE_JET_RIGHT = "right_side_jet_right"


def _right_side_jet_right(tracking: pd.DataFrame) -> bool:
    SPEED_THRESH = 2

    initial_x = tracking["x"].iloc[0]
    final_x = tracking["x"].iloc[-1]
    final_speed = tracking["s"].iloc[-1]

    if (
        initial_x > 0
        and final_x > 0
        and final_x > initial_x
        and final_speed > SPEED_THRESH
    ):
        return True
    else:
        return False


BACKFIELD_RIGHT_SET = "backfield_right_set"


def _backfield_right_set(tracking: pd.DataFrame) -> bool:
    X_THRESH = 2.5
    SPEED_THRESH = 2

    initial_x = tracking["x"].iloc[0]
    final_x = tracking["x"].iloc[-1]
    final_speed = tracking["s"].iloc[-1]

    if (
        initial_x < X_THRESH
        and initial_x > -X_THRESH
        and final_x > X_THRESH
        and final_speed < SPEED_THRESH
    ):
        return True
    else:
        return False


BACKFIELD_LEFT_SET = "backfield_left_set"


def _backfield_left_set(tracking: pd.DataFrame) -> bool:
    X_THRESH = 2.5
    SPEED_THRESH = 2

    initial_x = tracking["x"].iloc[0]
    final_x = tracking["x"].iloc[-1]
    final_speed = tracking["s"].iloc[-1]

    if (
        initial_x < X_THRESH
        and initial_x > -X_THRESH
        and final_x < -X_THRESH
        and final_speed < SPEED_THRESH
    ):
        return True
    else:
        return False


BACKFIELD_RIGHT_JET = "backfield_right_jet"


def _backfield_right_jet(tracking: pd.DataFrame) -> bool:
    X_THRESH = 2.5
    SPEED_THRESH = 2
    V_X_THRESH = 2

    initial_x = tracking["x"].iloc[0]
    final_x = tracking["x"].iloc[-1]
    final_speed = tracking["s"].iloc[-1]
    final_v_x = tracking["v_x"].iloc[-1]

    if (
        initial_x < X_THRESH
        and initial_x > -X_THRESH
        and final_x > X_THRESH
        and final_speed > SPEED_THRESH
        and final_v_x > V_X_THRESH
    ):
        return True
    else:
        return False


BACKFIELD_LEFT_JET = "backfield_left_jet"


def _backfield_left_jet(tracking: pd.DataFrame) -> bool:
    X_THRESH = 2.5
    SPEED_THRESH = 2
    V_X_THRESH = -2

    initial_x = tracking["x"].iloc[0]
    final_x = tracking["x"].iloc[-1]
    final_speed = tracking["s"].iloc[-1]
    final_v_x = tracking["v_x"].iloc[-1]

    if (
        initial_x < X_THRESH
        and initial_x > -X_THRESH
        and final_x < X_THRESH
        and final_speed > SPEED_THRESH
        and final_v_x < V_X_THRESH
    ):
        return True
    else:
        return False


def _classify_motion(tracking: pd.DataFrame) -> str:
    motion_types = []
    if _crossover_left_jet(tracking):
        motion_types.append(CROSSOVER_LEFT_JET)
    if _crossover_right_jet(tracking):
        motion_types.append(CROSSOVER_RIGHT_JET)
    if _crossover_left_set(tracking):
        motion_types.append(CROSSOVER_LEFT_SET)
    if _crossover_right_set(tracking):
        motion_types.append(CROSSOVER_RIGHT_SET)
    if _left_side_shift_left(tracking):
        motion_types.append(LEFT_SIDE_SHIFT_LEFT)
    if _left_side_shift_right(tracking):
        motion_types.append(LEFT_SIDE_SHIFT_RIGHT)
    if _right_side_shift_left(tracking):
        motion_types.append(RIGHT_SIDE_SHIFT_LEFT)
    if _right_side_shift_right(tracking):
        motion_types.append(RIGHT_SIDE_SHIFT_RIGHT)
    if _left_side_jet_left(tracking):
        motion_types.append(LEFT_SIDE_JET_LEFT)
    if _left_side_jet_right(tracking):
        motion_types.append(LEFT_SIDE_JET_RIGHT)
    if _right_side_jet_left(tracking):
        motion_types.append(RIGHT_SIDE_JET_LEFT)
    if _right_side_jet_right(tracking):
        motion_types.append(RIGHT_SIDE_JET_RIGHT)
    if _backfield_right_set(tracking):
        motion_types.append(BACKFIELD_RIGHT_SET)
    if _backfield_left_set(tracking):
        motion_types.append(BACKFIELD_LEFT_SET)
    if _backfield_right_jet(tracking):
        motion_types.append(BACKFIELD_RIGHT_JET)
    if _backfield_left_jet(tracking):
        motion_types.append(BACKFIELD_LEFT_JET)

    if len(motion_types) == 0:
        return "unclassified"
    else:
        return "|".join(motion_types)


def append_premotion_classification(force_calc: bool = False):
    # load in the data
    player_play = pd.read_csv(os.path.join(data.DATA_DIR, "player_play.csv"))

    # if the column already exists and we do not force calculation, there is nothing to do
    if not force_calc and CLASSIFICATION_COLUMN_NAME in player_play.columns:
        return

    # get premotioning player plays
    shifted = player_play["shiftSinceLineset"] == 1
    motioned = player_play["motionSinceLineset"] == 1
    pre_motion = player_play[shifted | motioned]
    pre_motion = pre_motion[["gameId", "playId", "nflId"]]

    # iterate over each pre-motioning player play and compute all metrics
    all_gids = pre_motion["gameId"].unique()
    for gid in tqdm.tqdm(all_gids, desc="Classifiying pre-motion player plays"):
        tracking = data.load_tracking_adjusted(gid)

        # compute the speed to be used by metric functions
        tracking["s"] = np.sqrt(tracking["v_x"] ** 2 + tracking["v_y"] ** 2)

        # get motion plays for this game
        player_play_game_mask = player_play["gameId"] == gid

        # get player play for this game
        pre_motion_game = pre_motion[pre_motion["gameId"] == gid]

        # iterate through each play
        all_pids = pre_motion_game["playId"].unique()
        for pid in all_pids:
            # players plays for this play
            pre_motion_play = pre_motion_game[pre_motion_game["playId"] == pid]

            # get the tracking for this play
            tracking_play = tracking[tracking["playId"] == pid]

            # get the player play play mask
            player_play_play_mask = player_play["playId"] == pid

            # iterate through each player
            all_nflids = pre_motion_play["nflId"].unique()
            for nflid in all_nflids:
                # get the frames for this player
                player_play_player_mask = player_play["nflId"] == nflid

                # get tracking for this play
                tracking_player = tracking_play[tracking_play["nflId"] == nflid]

                # get frames during motion
                start_frame_df = tracking_player.loc[
                    tracking_player[MOTION_EVENT_COLUMN_NAME] == "motion_start",
                    "frameId",
                ]
                end_frame_df = tracking_player.loc[
                    tracking_player[MOTION_EVENT_COLUMN_NAME] == "motion_end",
                    "frameId",
                ]

                if not (len(start_frame_df) > 0 and len(end_frame_df) > 0):
                    continue

                start_frame = start_frame_df.iloc[0]
                end_frame = end_frame_df.iloc[0]

                # get tracking between these frames
                tracking_frames = tracking_player[
                    (tracking_player["frameId"] >= start_frame)
                    & (tracking_player["frameId"] <= end_frame)
                ]

                motion_type = _classify_motion(tracking_frames)

                player_play.loc[
                    player_play_game_mask
                    & player_play_play_mask
                    & player_play_player_mask,
                    CLASSIFICATION_COLUMN_NAME,
                ] = motion_type

    # write the new player play data
    player_play.to_csv(os.path.join(data.DATA_DIR, "player_play.csv"))
