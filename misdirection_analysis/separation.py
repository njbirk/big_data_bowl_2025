from . import data
import os
import pandas as pd
import tqdm
import numpy as np
from scipy import optimize
from scipy.special import gamma


SEPARATION_COLUMN_NAME = "separation"


# ===================== #
# SEPARATION DATA FILES #
# ===================== #


def _compute_separation_metric(
    receiver: pd.DataFrame, defender: pd.DataFrame
) -> pd.Series:
    # compute the separation metric
    separation_x = receiver["x"].values - defender["x"].values
    separation_y = receiver["y"].values - defender["y"].values
    separation = np.sqrt(separation_x**2 + separation_y**2)

    return separation


def _separation_files_path(gid: int, sepbase_id: str = "main"):
    return os.path.join(data._PARQ_DIR, f"separation-metric-{sepbase_id}={gid}.parq")


def _create_separation_files(recalc: bool = False, sepbase_id: str = "main"):
    """
    Create the separation files.

    Pass a separation database ID if testing and wish to not overwrite the main.
    """
    # check if the files exist
    path = _separation_files_path(2022090800, sepbase_id)
    if not recalc and os.path.exists(path):
        return

    # load in the data
    games = pd.read_csv(os.path.join(data.DATA_DIR, "games.csv"))
    plays = pd.read_csv(os.path.join(data.DATA_DIR, "plays.csv"))
    player_play = pd.read_csv(os.path.join(data.DATA_DIR, "player_play.csv"))
    players = pd.read_csv(os.path.join(data.DATA_DIR, "players.csv"))

    # get position groups for player plays
    players = data.get_postion_groups(players)
    player_play = pd.merge(player_play, players[["nflId", "position_group"]])

    # iterate through each adjusted tracking game file
    all_gids = games["gameId"].unique()
    for gid in tqdm.tqdm(all_gids, desc="Calculating separation data files"):
        tracking = data.load_tracking_adjusted(gid)

        # intialize the arrays
        frame_array = np.array([])
        plays_array = np.array([])
        separation_array = np.array([])
        receiver_array = np.array([])
        defender_array = np.array([])

        # get plays for this game
        plays_game_mask = plays["gameId"] == gid
        plays_game = plays[plays_game_mask]

        # get only player play data for this game
        player_play_game_mask = player_play["gameId"] == gid
        player_play_game = player_play[player_play_game_mask]

        # iterate over each play
        all_pids = tracking["playId"].unique()
        for pid in all_pids:
            # get this play
            play = plays_game[plays_game["playId"] == pid].squeeze()

            # if not a passing play, continue to next play
            if not play["isDropback"]:
                continue

            # get frames for this play
            tracking_play_mask = tracking["playId"] == pid
            tracking_play: pd.DataFrame = tracking[tracking_play_mask]

            # get player plays for this play
            player_play_play_mask = player_play_game["playId"] == pid
            player_play_play: pd.DataFrame = player_play_game[player_play_play_mask]

            # get potential recievers for this play (running_back, tight_end, receiver)
            receiver_mask = player_play_play["position_group"].isin(
                ["running_back", "tight_end", "receiver"]
            )
            receiverIds = player_play_play.loc[receiver_mask, "nflId"].values

            # get potential defenders for this play (saftey, cornerback, linebacker)
            defender_mask = player_play_play["position_group"].isin(
                ["safety", "cornerback", "linebacker"]
            )
            defenderIds = player_play_play.loc[defender_mask, "nflId"].values

            # get frames for relevant players
            players_mask = tracking_play["nflId"].isin(
                np.concatenate((receiverIds, defenderIds))
            )
            tracking_relevant = tracking_play[players_mask]

            # get the frames for the quarterback
            qb_mask = player_play_play["position_group"] == "quarterback"
            qbId = player_play_play.loc[qb_mask, "nflId"].values[0]
            qb_mask = tracking_play["nflId"] == qbId
            tracking_qb: pd.DataFrame = tracking_play[qb_mask]

            # get the index of snap and ball thrown, scramble, or sack
            snap_frame = tracking_qb.loc[
                tracking_qb["event"].isin(["ball_snap", "snap_direct"]), "frameId"
            ].iloc[0]
            end_mask = tracking_qb["event"].isin(
                [
                    "pass_forward",
                    "qb_sack",
                    "fumble",
                    "pass_shovel",
                    "qb_slide",
                    "safety",
                    "lateral",
                    "run",
                    "qb_spike",
                    "pass_tipped",
                    "qb_strip_sack",
                    "pass_outcome_caught",
                    "fumble_offense_recovered",
                    "fumble_defense_recovered",
                    "autoevent_passinterrupted",
                ]
            )
            end_frame = tracking_qb.index[-1]
            if sum(end_mask) > 0:
                end_frame = tracking_qb.loc[
                    end_mask,
                    "frameId",
                ].iloc[0]

            # get the mask for only frames after snap and before end index
            after_snap_mask = tracking_relevant["frameId"] >= snap_frame
            before_end_mask = tracking_relevant["frameId"] <= end_frame

            # get each receivers frames
            receiver_frames = []
            for receiver in receiverIds:
                mask = tracking_relevant["nflId"] == receiver
                tracking_receiver = tracking_relevant[
                    mask & after_snap_mask & before_end_mask
                ]
                receiver_frames.append(tracking_receiver)

            # get the defenders frames
            defender_frames = []
            for defender in defenderIds:
                mask = tracking_relevant["nflId"] == defender
                tracking_defender = tracking_relevant[
                    mask & after_snap_mask & before_end_mask
                ]
                defender_frames.append(tracking_defender)

            # create the frame dictionaries
            receivers_dict = dict(zip(receiverIds, receiver_frames))
            defenders_dict = dict(zip(defenderIds, defender_frames))

            # calculate the separation for each receiver-defender combo
            for receiverId, receiver in receivers_dict.items():
                for defenderId, defender in defenders_dict.items():
                    this_separation_array = _compute_separation_metric(
                        receiver, defender
                    )
                    this_receiver_array = [
                        receiverId for _ in range(len(this_separation_array))
                    ]
                    this_defender_array = [
                        defenderId for _ in range(len(this_separation_array))
                    ]
                    this_plays_array = [pid for _ in range(len(this_separation_array))]
                    frame_array = np.concatenate(
                        (frame_array, receiver["frameId"].values)
                    )
                    separation_array = np.concatenate(
                        (separation_array, this_separation_array)
                    )
                    receiver_array = np.concatenate(
                        (receiver_array, this_receiver_array)
                    )
                    defender_array = np.concatenate(
                        (defender_array, this_defender_array)
                    )
                    plays_array = np.concatenate((plays_array, this_plays_array))

        # create the separation dataframe
        separation_frame = pd.DataFrame(
            {
                "frameId": frame_array,
                "playId": plays_array,
                "receiverId": receiver_array,
                "defenderId": defender_array,
                SEPARATION_COLUMN_NAME: separation_array,
            }
        )

        # write to file
        separation_frame.to_parquet(_separation_files_path(gid, sepbase_id))


# =================================== #
# SEPARATION PROBABILITY CALCULATIONS #
# =================================== #


def _compute_separation_probability(separation: np.ndarray) -> np.ndarray:
    return separation


def _emp_dist_data_path(sepbase_id: str = "main"):
    return os.path.join(data._PARQ_DIR, f"separation-emp-dist-{sepbase_id}.parq")


def _compute_emp_dist_data(recalc: bool = False, sepbase_id: str = "main"):
    # check if the files exist
    path = _emp_dist_data_path(sepbase_id)
    if not recalc and os.path.exists(path):
        return

    # load in the data
    games = pd.read_csv(os.path.join(data.DATA_DIR, "games.csv"))
    player_play = pd.read_csv(os.path.join(data.DATA_DIR, "player_play.csv"))

    # get player play where player targetted
    was_target_mask = player_play["wasTargettedReceiver"] == 1
    player_play_target = player_play[was_target_mask]

    # iterate through games
    all_gids = games["gameId"].unique()
    separation_dist_data = {"gameId": [], "playId": [], "values": [], "outcome": []}
    for gid in tqdm.tqdm(
        all_gids, desc="Getting empirical separation distribution data"
    ):
        # load the data
        separation_data = pd.read_parquet(_separation_files_path(gid, sepbase_id))

        # get player play target for this game
        player_play_game_mask = player_play_target["gameId"] == gid
        player_play_game = player_play_target[player_play_game_mask]

        # iterate through each pass play
        pid_recep = player_play_game[["playId", "hadPassReception"]].drop_duplicates()
        for _, row in pid_recep.iterrows():
            # check if the play is in the separation data
            if not row["playId"] in separation_data["playId"]:
                continue

            # get the separation data for this play
            separation_play_mask = separation_data["playId"] == row["playId"]
            separation_play = separation_data[separation_play_mask]

            # iterate through each defender
            all_defenders = separation_play["defenderId"].unique()
            for defender in all_defenders:
                # get the separation data for the defender
                defender_mask = separation_play["defenderId"] == defender
                separation_defender = separation_play[defender_mask]

                # get the final separation calculation
                separation_dist_data["values"].append(
                    float(separation_defender[SEPARATION_COLUMN_NAME].values[-1])
                )
                separation_dist_data["playId"].append(row["playId"])
                separation_dist_data["gameId"].append(gid)
                separation_dist_data["outcome"].append(row["hadPassReception"])

    # convert the dist data to a pd.DataFrame and write
    dist_data = pd.DataFrame(separation_dist_data)
    dist_data.to_parquet(_emp_dist_data_path(sepbase_id))


def _logig_func(x: pd.Series, a: float, b: float) -> pd.Series:
    return 2 * b / (1 + np.exp(a * x))


def _compute_error(params: np.ndarray, emp_dist_data: pd.DataFrame) -> float:
    """
    Minimization objective function
    """
    # get alpha and lambda_
    a = params[0]
    b = params[1]

    # compute the pdf
    emp_dist_data["probability"] = _logig_func(emp_dist_data["values"], a, b)

    # get probability not defend
    emp_dist_data["probability"] = 1 - emp_dist_data["probability"]

    # product out each probability
    df = emp_dist_data.groupby(["gameId", "playId"]).prod()

    # compute the correlation
    error = 1 - np.corrcoef(df["outcome"].values, df["probability"].values)[0, 1]

    return error


INITIAL_GUESS = [0.7, 1]


def _compute_emp_dist(sepbase_id: str = "main") -> list[float]:
    # get the empiracal separation data
    emp_dist_data = pd.read_parquet(_emp_dist_data_path(sepbase_id))

    # define the bounds
    bounds = [(0, None), (0, 1)]

    # find the minimum
    optimal = optimize.minimize(
        fun=_compute_error, x0=INITIAL_GUESS, args=(emp_dist_data), bounds=bounds
    )

    return optimal.x


def _compute_separation_probability(
    separation_data: pd.DataFrame, params: list[int]
) -> pd.DataFrame:
    # get alpha and lambda_
    a = params[0]
    b = params[1]

    # compute the pdf
    separation_data["probability"] = _logig_func(
        separation_data[SEPARATION_COLUMN_NAME], a, b
    )

    # get probability not defend
    separation_data["probability"] = 1 - separation_data["probability"]

    # product out each probability
    separation_data = separation_data.groupby(["playId", "receiverId", "frameId"])[
        "probability"
    ].prod()

    return separation_data


def append_separation_probability(force_calc: bool = False, sepbase_id: str = "main"):
    """
    Calculate separation and append the separation column to the adjusted tracking data.

    Pass `force_calc = True` to force the separation column to be recalculated even if it exists.
    """
    # create the separation files
    _create_separation_files(force_calc, sepbase_id)

    # create the empircal distribution files
    _compute_emp_dist_data(force_calc, sepbase_id)

    # compute the empircal distribution
    params = _compute_emp_dist(sepbase_id)

    # load in the data
    games = pd.read_csv(os.path.join(data.DATA_DIR, "games.csv"))

    # iterate through each adjusted tracking game file
    all_gids = games["gameId"].unique()
    with tqdm.tqdm(
        total=len(all_gids), desc="Calculating separation tracking column"
    ) as pbar:
        for gid in all_gids:
            tracking = data.load_tracking_adjusted(gid)
            separation_data = pd.read_parquet(_separation_files_path(gid, sepbase_id))

            # if the separation column already exists and we do not force_calc is False, there is nothing more to be done - return
            if SEPARATION_COLUMN_NAME in tracking.columns and not force_calc:
                pbar.n = len(all_gids)
                pbar.last_print_n = len(all_gids)
                pbar.update(0)
                return

            # compute the separation probability
            separation_data = _compute_separation_probability(
                separation_data, params
            ).reset_index()

            # initialize separation column
            tracking[SEPARATION_COLUMN_NAME] = None

            # iterate over each play
            all_pids = separation_data["playId"].unique()
            for pid in all_pids:
                # compute the tracking play mask
                tracking_play_mask = tracking["playId"] == pid

                # get separation metric for this play
                separation_play_mask = separation_data["playId"] == pid
                separation_play = separation_data[separation_play_mask]

                # create the frame Id mask
                tracking_frame_mask = tracking["frameId"].isin(
                    separation_play["frameId"].unique()
                )

                # iterate through each receiver
                all_receivers = separation_play["receiverId"].unique()
                for receiver in all_receivers:
                    separation = separation_play[
                        separation_play["receiverId"] == receiver
                    ]

                    # set the tracking data separation column
                    tracking_receiver_mask = tracking["nflId"] == receiver
                    tracking.loc[
                        tracking_play_mask
                        & tracking_receiver_mask
                        & tracking_frame_mask,
                        SEPARATION_COLUMN_NAME,
                    ] = separation["probability"].values
            pbar.update(1)

            # write the new adjusted tracking data with the separation column
            tracking.to_parquet(data.tracking_adjusted_path(gid))
