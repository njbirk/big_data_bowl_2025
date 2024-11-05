import pandas
import numpy
import os
import seaborn
from matplotlib import pyplot
from plotly import graph_objects

_DATA_DIR = "data/"

_COLORS = {
    "ARI": ["#97233F", "#000000", "#FFB612"],
    "ATL": ["#A71930", "#000000", "#A5ACAF"],
    "BAL": ["#241773", "#000000"],
    "BUF": ["#00338D", "#C60C30"],
    "CAR": ["#0085CA", "#101820", "#BFC0BF"],
    "CHI": ["#0B162A", "#C83803"],
    "CIN": ["#FB4F14", "#000000"],
    "CLE": ["#311D00", "#FF3C00"],
    "DAL": ["#003594", "#041E42", "#869397"],
    "DEN": ["#FB4F14", "#002244"],
    "DET": ["#0076B6", "#B0B7BC", "#000000"],
    "GB": ["#203731", "#FFB612"],
    "HOU": ["#03202F", "#A71930"],
    "IND": ["#002C5F", "#A2AAAD"],
    "JAX": ["#101820", "#D7A22A", "#9F792C"],
    "KC": ["#E31837", "#FFB81C"],
    "LA": ["#003594", "#FFA300", "#FF8200"],
    "LAC": ["#0080C6", "#FFC20E", "#FFFFFF"],
    "LV": ["#000000", "#A5ACAF"],
    "MIA": ["#008E97", "#FC4C02", "#005778"],
    "MIN": ["#4F2683", "#FFC62F"],
    "NE": ["#002244", "#C60C30", "#B0B7BC"],
    "NO": ["#101820", "#D3BC8D"],
    "NYG": ["#0B2265", "#A71930", "#A5ACAF"],
    "NYJ": ["#125740", "#000000", "#FFFFFF"],
    "PHI": ["#004C54", "#A5ACAF", "#ACC0C6"],
    "PIT": ["#FFB612", "#101820"],
    "SEA": ["#002244", "#69BE28", "#A5ACAF"],
    "SF": ["#AA0000", "#B3995D"],
    "TB": ["#D50A0A", "#FF7900", "#0A0A08"],
    "TEN": ["#0C2340", "#4B92DB", "#C8102E"],
    "WAS": ["#5A1414", "#FFB612"],
    "football": ["#CBB67C", "#663831"],
}


def _load_tracking(
    gameID: int,
    playID: int,
    tracking: pandas.DataFrame | None,
    selected_game: pandas.Series,
) -> pandas.DataFrame:
    if not isinstance(tracking, pandas.DataFrame):
        week = selected_game["week"]
        tracking = pandas.read_csv(
            os.path.join(_DATA_DIR, "tracking_week_" + str(week) + ".csv")
        )
    selected_tracking = tracking[
        (tracking["gameId"] == gameID) & (tracking["playId"] == playID)
    ]
    return selected_tracking


def _load_game(
    gameID: int,
    games: pandas.DataFrame | None,
) -> pandas.Series:
    if not isinstance(games, pandas.DataFrame):
        games = pandas.read_csv(os.path.join(_DATA_DIR, "games.csv"))
    selected_game = games.loc[games["gameId"] == gameID].iloc[0]
    return selected_game


def _load_play(
    gameID: int,
    playID: int,
    plays: pandas.DataFrame | None,
) -> pandas.Series:
    if not isinstance(plays, pandas.DataFrame):
        plays = pandas.read_csv(os.path.join(_DATA_DIR, "plays.csv"))
    selected_play = plays.loc[
        (plays["gameId"] == gameID) & (plays["playId"] == playID)
    ].iloc[0]
    return selected_play


def _load_players():
    pass


def animate_play(
    gameID: int,
    playID: int,
    games: pandas.DataFrame | None = None,
    plays: pandas.DataFrame | None = None,
    players: pandas.DataFrame | None = None,
    tracking: pandas.DataFrame | None = None,
):
    selected_game = _load_game(gameID, games)
    selected_play = _load_play(gameID, playID, plays)
    selected_tracking = _load_tracking(gameID, playID, tracking, selected_game)
    print(selected_game)
    print(selected_play)
    print(selected_tracking)


gid = 2022090800
pid = 2688

animate_play(gid, pid)
