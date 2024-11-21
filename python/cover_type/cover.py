import pandas as pd
from .. import data


def _runs_route(frames: pd.DataFrame) -> bool:
    return True


def detect_cover(
    gid: int,
    pid: int,
    tracking: pd.DataFrame | None = None,
    plays: pd.DataFrame | None = None,
):
    # if the tracking or plays data is not give, load it in
    if not isinstance(tracking, pd.DataFrame):
        tracking = data.load_tracking(gid)
    if not isinstance(plays, pd.DataFrame):
        plays = pd.read_csv("data/plays.csv")

    # get frames for the current play
    this_game = tracking["gameId"] == gid
    this_play = tracking["playId"] == pid
    frames = tracking[this_game & this_play].copy()

    # get pd.Series for this play
    this_game = plays["gameId"] == gid
    this_play = plays["playId"] == pid
    play = plays[this_game & this_play].iloc[0]

    # get the possesion team
    pos_team = play["possessionTeam"]

    # get the line of scrimmage x coordinate
    los_x = play["absoluteYardlineNumber"]

    # make line of scrimmage at x = 0
    if frames.iloc[0]["playDirection"] == "left":
        frames["x"] = 120 - frames["x"]
        los_x = 120 - los_x
    frames["x"] -= los_x

    # get nflId of possession team plays
    pos_team = frames["club"] == pos_team
    pos_frames = frames[pos_team]
    all_ids = pos_frames["nflId"].unique()

    # get nflId of players that run a route
    receivers = []
    for nflid in all_ids:
        this_player = pos_frames["nflId"] == nflid
        if _runs_route(pos_frames[this_player]):
            receivers.append(int(nflid))
    print(receivers)
    pass
