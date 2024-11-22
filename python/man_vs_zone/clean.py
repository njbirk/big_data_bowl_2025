import pandas as pd
import numpy as np


def get_postion_groups(players):
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


def flip_coords(tracking):
    """
    Flips the coordinates of the players on the left side of the field
    """

    mask = tracking["playDirection"] == "left"

    tracking.loc[mask, "x"] = 120 - tracking.loc[mask, "x"]
    tracking.loc[mask, "y"] = 160 / 3 - tracking.loc[mask, "y"]
    tracking.loc[mask, "o"] = (tracking.loc[mask, "o"] + 180) % 360
    tracking.loc[mask, "dir"] = (tracking.loc[mask, "dir"] + 180) % 360

    return tracking


def zero_coords(tracking, plays):
    """
    Adjusts the coordinates of the players to be relative to the line of scrimmage
    """

    for _, row in plays.iterrows():
        gid = row["gameId"]
        pid = row["playId"]

        # Apply the adjustment only to the relevant rows in tracking
        mask = (tracking["gameId"] == gid) & (tracking["playId"] == pid)
        tracking.loc[mask, "x"] -= row["absoluteYardlineNumber"]

    return tracking
