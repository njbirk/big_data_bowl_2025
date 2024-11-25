import pandas as pd
from scipy.interpolate import UnivariateSpline
import matplotlib.pyplot as plt
import numpy as np


def get_motion_start(
    gid: int,
    pid: int,
    nflid: int,
    tracking: pd.DataFrame,
    smoothing_param: float = 0.4,
    plot: bool = False,
) -> int:
    """
    Get the motion start based on the players maximum jerk before the snap.
    The spline curve smoothing parameter is set a 0.4 but can be optimized.
    """
    # get the selected player frames before the snap
    this_game = tracking["gameId"] == gid
    this_play = tracking["playId"] == pid
    this_player = tracking["nflId"] == nflid
    before_snap = tracking["frameType"] == "BEFORE_SNAP"
    frames = tracking[this_game & this_play & this_player & before_snap]

    # fit a cubic spline to the player speed data
    spline = UnivariateSpline(
        frames["frameId"].values, frames["s"].values, s=smoothing_param
    )

    # get the frameId with the maximum jerk
    frameIds = frames["frameId"].values
    index = np.argmax(spline(frameIds, 2))
    frameId_max = frameIds[index]

    # show the plot if told to
    if plot:
        X = np.arange(min(frameIds), max(frameIds), 0.1)
        plt.plot(X, spline(X), color="black")
        plt.plot(X, spline(X, 1), color="blue")
        plt.plot(X, spline(X, 2), color="green")
        plt.axvline(x=frameId_max, color="red")
        plt.show()

    # return the motion start
    return frameId_max
