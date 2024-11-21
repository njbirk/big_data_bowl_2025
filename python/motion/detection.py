import pandas as pd


def is_in_motion(tracking: pd.DataFrame, players: pd.DataFrame | None = None):
    # if the players data does not exists, load it in
    if not isinstance(players, pd.DataFrame):
        players = pd.read_csv("data/players.csv")

    # is the player a WR
    is_wr = tracking["nflid"].isin(players[players["position"] == "WR"]["nflid"])

    motion = is_wr

    #return 
    return motion
