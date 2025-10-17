# Copyright (c) 2024 Cloudflare, Inc.
# Licensed under the Apache 2.0 license found in the LICENSE file or at https://www.apache.org/licenses/LICENSE-2.0

import time

from . import const

class DataSampleEvaluatorClass:

    # args are client args
    def __init__(self, args0):
        self.args = args0
        self.valid_flag = False
        self.max_ramp_time = self.args.max_ramp_time

        if not self.max_ramp_time:
            if self.args.udp:
                self.max_ramp_time = const.DATA_SAMPLE_IGNORE_TIME_UDP_MAX_SEC
            else:
                self.max_ramp_time = const.DATA_SAMPLE_IGNORE_TIME_TCP_MAX_SEC

        if self.args.verbosity:
            print("max_ramp_time is {}".format(self.max_ramp_time), flush=True)


    # once a sample is valid then all subsequent samples are valid
    def is_sample_valid(self, run_mode_running_start_time, dropped_this_interval_percent, curr_time):
        if self.valid_flag:
            return True

        # samples are never valid until we have passed the "ignore time"
        if curr_time < (run_mode_running_start_time + const.DATA_SAMPLE_IGNORE_TIME_ALWAYS_SEC):
            return False

        # udp -- can we exit early?
        if self.args.udp:
            if dropped_this_interval_percent > 0:
                self.valid_flag = True
                return True

        if curr_time > (run_mode_running_start_time + self.max_ramp_time):
            self.valid_flag = True
            return True

        return False

