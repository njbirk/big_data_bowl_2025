from . import data
import pandas as pd
import os
import tqdm
from .motion_detection import MOTION_EVENT_COLUMN_NAME
import numpy as np
import datetime
from . import data


#                                    # ================== #                                    #
# ================================== # METRIC COMPUTATION # ================================== #
#                                    # ================== #                                    #


# ================= #
# Distance Traveled #
# ================= #


DISTANCE_X = "distance_x"


def _distance_x_metric(
    tracking: pd.DataFrame, motion_start: int, motion_end: int, snap: int
) -> float:
    start_x = tracking.loc[motion_start, "x"]
    end_x = tracking.loc[motion_end, "x"]
    return end_x - start_x


DISTANCE_Y = "distance_y"


def _distance_y_metric(
    tracking: pd.DataFrame, motion_start: int, motion_end: int, snap: int
) -> float:
    start_y = tracking.loc[motion_start, "y"]
    end_y = tracking.loc[motion_end, "y"]
    return end_y - start_y


TOTAL_DISTANCE = "total_distance"


def _total_distance_metric(
    tracking: pd.DataFrame, motion_start: int, motion_end: int, snap: int
) -> float:
    start_x = tracking.loc[motion_start, "x"]
    end_x = tracking.loc[motion_end, "x"]
    start_y = tracking.loc[motion_start, "y"]
    end_y = tracking.loc[motion_end, "y"]
    return np.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)


# ===== #
# Speed #
# ===== #


AVERAGE_SPEED = "average_speed"


def _average_speed_metric(
    tracking: pd.DataFrame, motion_start: int, motion_end: int, snap: int
) -> float:
    start_x = tracking.loc[motion_start, "x"]
    end_x = tracking.loc[motion_end, "x"]
    start_y = tracking.loc[motion_start, "y"]
    end_y = tracking.loc[motion_end, "y"]
    distance = np.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)
    return distance / ((motion_end - motion_start) * 0.1)


MAX_SPEED = "max_speed"


def _max_speed_metric(
    tracking: pd.DataFrame, motion_start: int, motion_end: int, snap: int
) -> float:
    return max(tracking["s"])


# ======== #
# Location #
# ======== #

INITIAL_X = "initial_x"


def _initial_x_metric(
    tracking: pd.DataFrame, motion_start: int, motion_end: int, snap: int
) -> float:
    return tracking.loc[motion_start, "x"]


INITIAL_Y = "initial_y"


def _initial_y_metric(
    tracking: pd.DataFrame, motion_start: int, motion_end: int, snap: int
) -> float:
    return tracking.loc[motion_start, "y"]


FINAL_X = "final_x"


def _final_x_metric(
    tracking: pd.DataFrame, motion_start: int, motion_end: int, snap: int
) -> float:
    return tracking.loc[motion_end, "x"]


FINAL_Y = "final_y"


def _final_y_metric(
    tracking: pd.DataFrame, motion_start: int, motion_end: int, snap: int
) -> float:
    return tracking.loc[motion_end, "y"]


# ====== #
# Timing #
# ====== #


SPEED_AT_SNAP = "speed_at_snap"


def _speed_at_snap_metric(
    tracking: pd.DataFrame, motion_start: int, motion_end: int, snap: int
) -> float:
    return tracking.loc[snap, "s"]


X_AT_SNAP = "x_at_snap"


def _x_at_snap_metric(
    tracking: pd.DataFrame, motion_start: int, motion_end: int, snap: int
) -> float:
    return tracking.loc[snap, "x"]


Y_AT_SNAP = "y_at_snap"


def _y_at_snap_metric(
    tracking: pd.DataFrame, motion_start: int, motion_end: int, snap: int
) -> float:
    return tracking.loc[snap, "y"]


# ====================== #
# Metric Master Function #
# ====================== #


METRIC_FUNCTIONS = {
    DISTANCE_X: _distance_x_metric,
    DISTANCE_Y: _distance_y_metric,
    TOTAL_DISTANCE: _total_distance_metric,
    AVERAGE_SPEED: _average_speed_metric,
    MAX_SPEED: _max_speed_metric,
    INITIAL_X: _initial_x_metric,
    INITIAL_Y: _initial_y_metric,
    FINAL_X: _final_x_metric,
    FINAL_Y: _final_y_metric,
    SPEED_AT_SNAP: _speed_at_snap_metric,
    X_AT_SNAP: _x_at_snap_metric,
    Y_AT_SNAP: _y_at_snap_metric,
}


def _get_metrics(tracking: pd.DataFrame, row: pd.Series) -> pd.Series:
    """
    Compute each metric for the given tracking and player play (row).
    """
    # get the tracking data for this player play
    this_play = tracking["playId"] == row["playId"]
    this_player = tracking["nflId"] == float(row["nflId"])
    tracking = tracking[this_play & this_player]

    # check that there was motion detection
    if not sum(tracking[MOTION_EVENT_COLUMN_NAME] == "motion_start"):
        return pd.Series()

    # get the indexes of motion start, end, and snap
    start_mask = tracking[MOTION_EVENT_COLUMN_NAME] == "motion_start"
    motion_start = tracking[start_mask].index[0]
    end_mask = tracking[MOTION_EVENT_COLUMN_NAME] == "motion_end"
    motion_end = tracking[end_mask].index[0]
    snap_mask = tracking["event"].isin(["ball_snap", "snap_direct"])
    snap = tracking[snap_mask].index[0]

    # iterate over all metrics and compute for the player play tracking data
    metrics = pd.Series()
    for metric_name, function in METRIC_FUNCTIONS.items():
        metrics[metric_name] = function(tracking, motion_start, motion_end, snap)

    return metrics


#                                    # ================ #                                    #
# ================================== # DATASET CREATION # ================================== #
#                                    # ================ #                                    #


# we populate a dictionary and convert to pd.DataFrame at the end for increased performance
DEFAULT_METRIC_DATA = {
    "gameId": [],
    "playId": [],
    "nflId": [],
    DISTANCE_X: [],
    DISTANCE_Y: [],
    TOTAL_DISTANCE: [],
    AVERAGE_SPEED: [],
    MAX_SPEED: [],
    INITIAL_X: [],
    INITIAL_Y: [],
    FINAL_X: [],
    FINAL_Y: [],
    SPEED_AT_SNAP: [],
    X_AT_SNAP: [],
    Y_AT_SNAP: [],
}


def create_dataset() -> str:
    """
    Create the pre-motion classification dataset.

    DataFrame has a row for each pre-motioning player play and a column for each defined metrics.

    Returns the path to the parquet file where the dataset is written.
    """
    # get all pre-motioning player plays
    player_play = pd.read_csv(os.path.join(data.DATA_DIR, "player_play.csv"))
    shifted = player_play["shiftSinceLineset"] == 1
    motioned = player_play["motionSinceLineset"] == 1
    pre_motion = player_play[shifted | motioned]
    pre_motion = pre_motion[["gameId", "playId", "nflId"]]

    # sort by the gameId so each game's tracking data is loaded only once when iterating
    pre_motion = pre_motion.sort_values(by="gameId")

    # iterate over each pre-motioning player play and compute all metrics
    current_gameId = None
    tracking = None
    metric_data = DEFAULT_METRIC_DATA.copy()
    for _, row in tqdm.tqdm(
        pre_motion.iterrows(),
        desc="Computing metrics for pre-motioning player plays",
        total=len(pre_motion),
    ):
        # check if we need to load in a new game tracking data
        if row["gameId"] != current_gameId:
            tracking = data.load_tracking_adjusted(row["gameId"])
            current_gameId = row["gameId"]

            # compute the speed to be used by metric functions
            tracking["s"] = np.sqrt(tracking["v_x"] ** 2 + tracking["v_y"] ** 2)

        # get the metrics for this player play
        row_metrics = _get_metrics(tracking, row)

        # if it is empty, there was no motion detection in the frame - continue to next player play
        if row_metrics.empty:
            continue

        # append the player play identifiers
        for index, value in row.items():
            metric_data[index].append(value)

        # get the metrics for this player play and append
        for index, value in row_metrics.items():
            metric_data[index].append(value)

    # convert the metric data to pd.DataFrame
    metric_data = pd.DataFrame(metric_data)

    # write the dataset to the data files with a timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(data._PARQ_DIR, f"dataset-motionclass-{timestamp}.parq")
    metric_data.to_parquet(path)
    return path
