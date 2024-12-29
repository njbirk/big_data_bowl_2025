import os
from . import data
from . import motion_detection


def setup():
    # create the parqs folder if it does not exist
    if not os.path.exists(data._PARQ_DIR):
        os.mkdir(data._PARQ_DIR)

    # create the raw tracking data
    data._create_tracking_raw()

    # create the adjusted tracking data
    data._create_tracking_adjusted()

    # run the lineset and motion detection
    motion_detection.append_motion_event()
