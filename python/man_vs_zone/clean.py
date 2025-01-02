import pandas as pd
import numpy as np
import networkx as nx

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


def get_postion_groups(players):
    """
    Assigns position groups to all players to make it easier to group them later
    """

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


def graph_one_play(tracking, gameId, playId, snap_type):
    """
    Creates a graph representation of a single play
    """

    frames = []

    play_data = tracking.loc[
        (tracking["gameId"] == gameId) & (tracking["playId"] == playId)
    ]

    frame_count = int(play_data["frameId"].max())

    snap = play_data.loc[play_data["frameType"] == "SNAP", "frameId"].iloc[0]

    if snap_type == "pre":
        begin = 0
        end = snap
    else:
        begin = snap
        end = frame_count + 1

    for frame in range(begin, end):
        temp = play_data.loc[play_data["frameId"] == frame]

        G = nx.Graph()

        for _, row in temp.iterrows():

            G.add_node(
                row["nflId"],
                position=row["position_group"],
                club=row["club"],
                x=row["x"],
                y=row["y"],
                s=row["s"],
                a=row["a"],
                dir=row["dir"],
            )

        CBs = [
            nflId
            for nflId, data in G.nodes(data=True)
            if data["position"] in ["cornerback"]
        ]

        WRs = [
            nflId
            for nflId, data in G.nodes(data=True)
            if data["position"] == "receiver"
        ]
        closest_pairs = []

        for CB in CBs:
            min_dist = float("inf")
            closest_WR = None
            for WR in WRs:
                dist = np.linalg.norm(
                    np.array([G.nodes[CB]["x"], G.nodes[CB]["y"]])
                    - np.array([G.nodes[WR]["x"], G.nodes[WR]["y"]])
                )
                if dist < min_dist:
                    min_dist = dist
                    closest_WR = WR
            closest_pairs.append((CB, closest_WR, min_dist))

        for CB, WR, dist in closest_pairs:
            G.add_edge(CB, WR, type="coverage", distance=dist)

        frames.append(G)

    return frames


def graph_all_plays(tracking, snap_type):
    """
    Creates a graph representation of all plays in the dataset
    """

    plays = {}
    unique_plays = tracking[["gameId", "playId"]].drop_duplicates()

    for row in unique_plays.itertuples(index=False):
        gid, pid = row.gameId, row.playId
        plays[(gid, pid)] = graph_one_play(tracking, gid, pid, snap_type)

    return plays
