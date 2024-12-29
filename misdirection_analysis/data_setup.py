import os
from . import data
from . import motion_detection


def setup():
    print("This function will complete 3 progress bars.")
    print("On Adam's MacBook Air M2:")
    print("\tpbar1: 92 seconds")
    print("\tpbar2: 91 seconds")
    print("\tpbar3: 168 seconds")
    print("\ttotal time: 5 minutes 51 seconds")

    # create the parqs folder if it does not exist
    if not os.path.exists(data._PARQ_DIR):
        os.mkdir(data._PARQ_DIR)

    # create the raw tracking data
    data._create_tracking_raw()

    # create the adjusted tracking data
    data._create_tracking_adjusted()

    # run the lineset and motion detection
    motion_detection.append_motion_event()
