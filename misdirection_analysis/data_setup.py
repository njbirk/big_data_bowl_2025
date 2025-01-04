import os
from . import data
from . import motion_detection
from . import separation
from . import separation_metric
from . import premotion_classify


def setup(force_calcs: bool = False):
    print("This function will complete 6 progress bars.")
    print("On Adam's MacBook Air M2:")
    print("\tpbar1: 91 seconds")
    print("\tpbar2: 89 seconds")
    print("\tpbar3: 121 seconds")
    print("\tpbar4: 154 seconds")
    print("\tpbar5: 20 seconds")
    print("\tpbar6: 108 seconds")
    print("\tpbar7: 46 seconds")
    print("\ttotal time: ~ 10 min")

    # create the parqs folder if it does not exist
    if not os.path.exists(data._PARQ_DIR):
        os.mkdir(data._PARQ_DIR)

    # create the raw tracking data
    data._create_tracking_raw(force_calcs)

    # create the adjusted tracking data
    data._create_tracking_adjusted(force_calcs)

    # run the lineset and motion detection
    motion_detection.append_motion_event(force_calcs)

    # append the separation probability
    separation.append_separation_probability(force_calcs)

    # run the premotion classification
    premotion_classify.append_premotion_classification(force_calcs)


def setup_clean(force_calcs: bool = False):
    print("This function will complete 4 progress bars.")
    print("On Adam's MacBook Air M2:")
    print("\tpbar1: 91 seconds")
    print("\tpbar2: 88 seconds")
    print("\tpbar3: 162 seconds")
    print("\tpbar4: 235 seconds")
    print("\tpbar5: 64 seconds")
    print("\ttotal time: ~ 10 min")

    # create the parqs folder if it does not exist
    if not os.path.exists(data._PARQ_DIR):
        os.mkdir(data._PARQ_DIR)

    # create the raw tracking data
    data._create_tracking_raw(force_calcs)

    # create the adjusted tracking data
    data._create_tracking_adjusted(force_calcs)

    # run the lineset and motion detection
    motion_detection.append_motion_event(force_calcs)

    # run the premotion classification
    premotion_classify.append_premotion_classification(force_calcs)

    # compute the separation metric
    separation_metric.append_separation_metric(force_calcs)

    # run the premotion classification
    premotion_classify.append_premotion_classification(force_calcs)
