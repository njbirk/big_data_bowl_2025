from . import data
import pandas as pd
import os


BOX_X_LEFT = -7
BOX_X_RIGHT = 7
BOX_Y = 7


def get_linebacker_motion_play(tracking: pd.DataFrame):
    # get the frame ID of the lineset
    lineset_frame = tracking.loc[
        tracking["motion_event"] == "lineset", "frameId"
    ].values[0]

    # get the linebackers positions at the lineset
    positions = tracking.loc[tracking["frameId"] == lineset_frame, ["nflId", "x", "y"]]

    # get linebackers in the box
    box_x_left = positions["x"] > BOX_X_LEFT
    box_x_right = positions["x"] < BOX_X_RIGHT
    box_y = positions["y"] < BOX_Y
    linebackers_in_box = positions.loc[box_x_left & box_x_right & box_y, "nflId"].values

    # if there are none, return None
    if len(linebackers_in_box) == 0:
        return None

    # get the tracking for linebackers in the box
    tracking_in_box = tracking[tracking["nflId"].isin(linebackers_in_box)]

    # get the frame ID of the snap
    snap_frame = tracking.loc[
        tracking["event"].isin(["snap_direct", "ball_snap"]), "frameId"
    ].values[0]

    # print the linebackers speed at snap
    df = tracking_in_box.loc[
        tracking_in_box["frameId"] == snap_frame,
        ["gameId", "playId", "nflId", "v_x", "v_y"],
    ]


def get_linebacker_motion():
    # load in the necessary data
    plays = pd.read_csv(os.path.join(data.DATA_DIR, "plays.csv"))
    players = pd.read_csv(os.path.join(data.DATA_DIR, "players.csv"))
    player_play = pd.read_csv(os.path.join(data.DATA_DIR, "player_play.csv"))

    # get position groups for players
    players = data.get_postion_groups(players)
    player_play = pd.merge(player_play, players[["nflId", "position_group"]])

    # get all linebackers
    linebackers = player_play.loc[
        player_play["position_group"].isin(["linebacker", "cornerback", "safety"]),
        "nflId",
    ].values

    # iterate through each game
    all_games = plays["gameId"].unique()
    for gid in all_games:
        # load the tracking for this game
        tracking = data.load_tracking_adjusted(gid)

        # get player plays for this game
        player_play_game = player_play[player_play["gameId"] == gid]

        # iterate through passing plays (isDropback)
        all_pids = plays.loc[
            (plays["gameId"] == gid) & (plays["isDropback"] == 1), "playId"
        ].values
        for pid in all_pids:
            # get linebackers for this play
            linebackers_play = player_play_game.loc[
                (player_play_game["playId"] == pid)
                & (player_play_game["nflId"].isin(linebackers)),
                "nflId",
            ].values

            # get linebacker tracking
            tracking_linebackers = tracking[
                (tracking["playId"] == pid) & tracking["nflId"].isin(linebackers_play)
            ]

            # get the linebacker motion for this play
            get_linebacker_motion_play(tracking_linebackers)
