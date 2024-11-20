import pandas as pd
from .. import data
import matplotlib.pyplot as plt


_ROUTE_COLORS = [
    "red",
    "blue",
    "green",
    "orange",
    "black",
    "purple",
    "cyan",
    "magenta",
    "yellow",
]


def _plot_player_route(nflid: int, frames: pd.DataFrame, route_index: int):
    # get frames for this player
    this_player = frames["nflId"] == nflid
    frames = frames[this_player]

    # plot the route
    displayName = frames.iloc[0]["displayName"]
    plt.plot(
        frames["y"],
        frames["x"] - 10,
        color=_ROUTE_COLORS[route_index],
        label=f"{displayName} (nflid: {nflid})",
    )


def plot_routes(
    gid: int,
    pid: int,
    tracking: pd.DataFrame | None = None,
    plays: pd.DataFrame | None = None,
    players: pd.DataFrame | None = None,
):
    # if the tracking, plays, or players data is not given load it in
    if not isinstance(tracking, pd.DataFrame):
        tracking = data.load_tracking(gid)
    if not isinstance(plays, pd.DataFrame):
        plays = pd.read_csv("data/plays.csv")
    if not isinstance(players, pd.DataFrame):
        players = pd.read_csv("data/players.csv")

    # get only the frames for this play
    this_game = tracking["gameId"] == gid
    this_play = tracking["playId"] == pid
    frames = tracking[this_game & this_play]

    # get frames between "ball_snap" and "pass_arrived"
    time_ball_snap = frames[frames["event"] == "ball_snap"]["time"].values[0]
    time_pass_arrived = frames[frames["event"] == "pass_arrived"]["time"].values[0]
    after_snap = frames["time"] >= time_ball_snap
    before_arrived = frames["time"] <= time_pass_arrived
    frames: pd.DataFrame = frames[after_snap & before_arrived].copy()

    # correct for play direction
    if frames["playDirection"].iloc[0] == "left":
        frames["x"] = 120 - frames["x"]
    else:
        frames["y"] = 53.3 - frames["y"]

    # get only the wide reciever frames
    nflids = []
    nflids_in_frame = frames[frames["nflId"].notna()]["nflId"].unique()
    for nflid in nflids_in_frame:
        pos = players[players["nflId"] == nflid].iloc[0]["position"]
        if pos == "WR" or pos == "TE" or pos == "RB":
            nflids.append(nflid)

    # plot each nflid
    count = 0
    for nflid in nflids:
        _plot_player_route(nflid, frames, count)
        count += 1

    # set the plot to the entire field dimensions
    plt.gca().set_aspect("equal")
    plt.xlim((0, 53.3))
    plt.ylim((-10, 110))

    # set the plot background color
    plt.gca().set_facecolor("lightgreen")

    # add the yardlines
    plt.axhline(y=0, color="red", linewidth=1)
    plt.axhline(y=10, color="black", linewidth=1)
    plt.axhline(y=20, color="black", linewidth=1)
    plt.axhline(y=30, color="black", linewidth=1)
    plt.axhline(y=40, color="black", linewidth=1)
    plt.axhline(y=50, color="black", linewidth=1)
    plt.axhline(y=60, color="black", linewidth=1)
    plt.axhline(y=70, color="black", linewidth=1)
    plt.axhline(y=80, color="black", linewidth=1)
    plt.axhline(y=90, color="black", linewidth=1)
    plt.axhline(y=100, color="red", linewidth=1)

    # add the line of scrimage and first down line
    this_game = plays["gameId"] == gid
    this_play = plays["playId"] == pid
    play = plays[this_game & this_play].iloc[0]
    los = 0
    if play["possessionTeam"] == play["yardlineSide"]:
        los = play["yardlineNumber"]
    else:
        los = 100 - play["yardlineNumber"]
    fdown = los + play["yardsToGo"]
    plt.axhline(y=los, color="blue", linewidth=1)
    plt.axhline(y=fdown, color="yellow", linewidth=1)

    # hide the axis number labels
    plt.xticks([])

    # add the legend to show which color is which player
    plt.legend(loc="center", bbox_to_anchor=(1.7, 0.8))

    # Show the plot
    plt.show()
