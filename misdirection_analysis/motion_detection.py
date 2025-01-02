import pandas as pd
from . import data
import os
from scipy.interpolate import UnivariateSpline
import numpy as np
import tqdm


# speed at which we assume the player is not moving
SPEED_THRESHOLD = 0.2

# minimum pre-snap frames we require to perform analysis
MINIMUM_PRE_SNAP_FRAMES = 10

# name of the motion event column
MOTION_EVENT_COLUMN_NAME = "motion_event"

# slope value (absolute value) of offensive average speed for which we round to zero
#       - used to determine the point at which a offense has stopped moving
SPEED_NO_SLOPE_THRESHOLD = 0.005

# average offensive y value for which we consider the offense plasuiby at lineset
#       - main purpose is to prevent us from accidentally classify huddle as a possible lineset
Y_LINESET_THRESHOLD = -5

# spline curve smoothing parameter
SMOOTHING_PARAM = 0.4


def _get_lineset_event(
    tracking: pd.DataFrame, smoothing_param: float = SMOOTHING_PARAM
) -> int:
    """
    Get the lineset frame ID
    """
    # get pre_snap frames
    snap_frame = tracking.loc[
        tracking["event"].isin(["ball_snap", "snap_direct"]), "frameId"
    ].iloc[0]
    pre_snap = tracking["frameId"] < snap_frame
    tracking = tracking[pre_snap]

    # get the average distance/speed group by
    groupby_view = tracking.groupby("frameId")[["y", "s"]].mean()

    # if there are not enough frames before the snap, return 1
    if len(groupby_view) < MINIMUM_PRE_SNAP_FRAMES:
        return 1

    # fit a spline to speed
    spline = UnivariateSpline(
        groupby_view.index.values, groupby_view["s"].values, s=0.4
    )

    # find the first frame where the spline's slope is 0, concavity is positive, and the Y is within the threshold
    lineset = None
    deriv1 = spline.derivative(1)
    deriv2 = spline.derivative(2)
    for frameId in groupby_view.index:
        if (
            abs(deriv1(frameId)) < SPEED_NO_SLOPE_THRESHOLD
            and deriv2(frameId) > 0
            and groupby_view.loc[frameId, "y"] > Y_LINESET_THRESHOLD
        ):
            lineset = frameId
            break

    if lineset:
        return lineset
    else:
        return 1


def _spline_method(
    tracking: pd.DataFrame, smoothing_param: float = SMOOTHING_PARAM
) -> int:
    """
    Fit a smoothing spline and return the first local jerk maxima.

    This is done by computing the jerk's critical values (roots of the 3rd derivative).
    """
    # fit the smoothing spline
    spline = UnivariateSpline(
        tracking["frameId"].values, tracking["s"].values, s=smoothing_param
    )

    # iterate through the frames until the first + -> - switch for the 3rd derivative
    #       - this indicates a jerk concavity switch from + -> - (aka a jerk local maxima)
    deriv3 = spline.derivative(3)
    is_positive = False
    maxima_frame = None
    for frameId in tracking["frameId"].values:
        if deriv3(frameId) < 0:
            if is_positive:
                maxima_frame = frameId - 1
                break
        else:
            is_positive = True

    # return first frame prior to jerk maxima where speed is above the threshold
    while spline(maxima_frame) > SPEED_THRESHOLD and maxima_frame > min(
        tracking["frameId"].values
    ):
        maxima_frame -= 1

    return maxima_frame


def _motion_start_frame(tracking: pd.DataFrame, lineset_frameId: int) -> int | None:
    """
    Compute the starting frame ID of motion
    """
    # get only frames between lineset and ball snap
    start_idx = tracking[tracking["frameId"] == lineset_frameId].index[0]
    ball_snap_idx = tracking[
        tracking["event"].isin(["ball_snap", "snap_direct"])
    ].index[0]
    tracking = tracking.loc[start_idx:ball_snap_idx]

    # check edge case when time before snap is very short
    if ball_snap_idx - start_idx < MINIMUM_PRE_SNAP_FRAMES:
        return None

    # get the motion start index using spline method
    start_frame = _spline_method(tracking)

    return start_frame


def _motion_end_frame(tracking: pd.DataFrame, start_frame: int) -> int:
    """
    Get the motion end frame.

    Define this as the first frame such that all frames after until the snap has a speed within the maximum speed threshold.
    """
    # frames after motion start but before ball snap
    start_frame_idx = tracking[tracking["frameId"] == start_frame].index[0]
    ball_snap_idx = tracking[
        tracking["event"].isin(["ball_snap", "snap_direct"])
    ].index[0]
    tracking = tracking.loc[start_frame_idx:ball_snap_idx]

    # end index is first frame which players speed is below threshold
    end_index = ball_snap_idx
    low_speed = tracking["s"] < SPEED_THRESHOLD
    for _ in range(0, len(low_speed) - 1):
        if low_speed.loc[end_index - 1]:
            end_index -= 1
        else:
            break

    if end_index:
        return tracking.loc[end_index, "frameId"]
    else:
        return tracking.loc[ball_snap_idx, "frameId"]


def append_motion_event(force_calc: bool = False):
    """
    Perform lineset detection and motion start/stop on the adjusted tracking data and
    appends the event column to the tracking data if it does not already exist.

    Pass `force_calc = True` to force the event column to be recalculated even if it exists.
    """
    # load in the data
    games = pd.read_csv(os.path.join(data.DATA_DIR, "games.csv"))
    plays = pd.read_csv(os.path.join(data.DATA_DIR, "plays.csv"))
    player_play = pd.read_csv(os.path.join(data.DATA_DIR, "player_play.csv"))

    # iterate through each adjusted tracking game file
    all_gids = games["gameId"].unique()
    with tqdm.tqdm(total=len(all_gids), desc="Calculating motion events") as pbar:
        for gid in all_gids:
            tracking = data.load_tracking_adjusted(gid)

            # compute speed
            tracking["s"] = np.sqrt(tracking["v_x"] ** 2 + tracking["v_y"] ** 2)

            # if the event column already exists and we do not force_calc is False, there is nothing more to be done - return
            if MOTION_EVENT_COLUMN_NAME in tracking.columns and not force_calc:
                pbar.n = len(all_gids)
                pbar.last_print_n = len(all_gids)
                pbar.update(0)
                return

            # initialize motion event column
            tracking[MOTION_EVENT_COLUMN_NAME] = None

            # get only player play data for this game
            player_play_game_mask = player_play["gameId"] == gid
            player_play_game = player_play[player_play_game_mask]

            # iterate over each play
            all_pids = tracking["playId"].unique()
            for pid in all_pids:
                # get the offensive team
                plays_game_mask = plays["gameId"] == gid
                plays_play_mask = plays["playId"] == pid
                offensive_club = plays.loc[
                    plays_game_mask & plays_play_mask, "possessionTeam"
                ].squeeze()

                # get offensive frames for this play
                tracking_play_mask = tracking["playId"] == pid
                play_frames = tracking[tracking_play_mask]
                play_frames_offense_mask = play_frames["club"] == offensive_club
                offensive_frames = play_frames[play_frames_offense_mask]

                # compute the lineset frameId
                lineset_frameId = _get_lineset_event(offensive_frames)

                # set the event column
                tracking_lineset_frame_mask = tracking["frameId"] == lineset_frameId
                tracking.loc[
                    tracking_play_mask & tracking_lineset_frame_mask,
                    MOTION_EVENT_COLUMN_NAME,
                ] = "lineset"

                # iterate through motion players on this play
                player_play_play_mask = player_play_game["playId"] == pid
                player_play_motion_mask = player_play_game["motionSinceLineset"] == 1
                all_nflids = player_play_game.loc[
                    player_play_play_mask & player_play_motion_mask, "nflId"
                ]

                for nflid in all_nflids:
                    # get the player play frames
                    offense_player_mask = offensive_frames["nflId"] == nflid
                    player_frames = offensive_frames[offense_player_mask]

                    # compute the motion start/stop frameIds
                    start_frameId = _motion_start_frame(player_frames, lineset_frameId)
                    if start_frameId:
                        end_frameId = _motion_end_frame(player_frames, start_frameId)

                        # set the event column
                        tracking_player_mask = tracking["nflId"] == nflid
                        start_frame = tracking["frameId"] == start_frameId
                        tracking.loc[
                            tracking_play_mask & tracking_player_mask & start_frame,
                            MOTION_EVENT_COLUMN_NAME,
                        ] = "motion_start"
                        end_frame = tracking["frameId"] == end_frameId
                        tracking.loc[
                            tracking_play_mask & tracking_player_mask & end_frame,
                            MOTION_EVENT_COLUMN_NAME,
                        ] = "motion_end"
            pbar.update(1)

            tracking.drop(columns=["s"])

            # write the new adjusted tracking data with the lineset event column
            tracking.to_parquet(data.tracking_adjusted_path(gid))
