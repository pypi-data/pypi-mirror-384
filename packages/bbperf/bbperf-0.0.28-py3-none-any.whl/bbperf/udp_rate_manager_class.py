# Copyright (c) 2024 Cloudflare, Inc.
# Licensed under the Apache 2.0 license found in the LICENSE file or at https://www.apache.org/licenses/LICENSE-2.0

import numpy

from . import const
from . import util

# this is a simple congestion control algorithm for the udp test
class UdpRateManagerClass:

    # args are client args
    def __init__(self, args, shared_udp_sending_rate_pps):
        self.args = args
        self.shared_udp_sending_rate_pps = shared_udp_sending_rate_pps
        self.receiver_pps_list = []
        self.last_new_rate = 0

    # control receiver calls this with interval pps (every 0.1 seconds)
    def update(self, r_record):
        # gut checks to avoid updating based on bogus input
        if r_record["r_sender_total_pkts_sent"] < 100:
            return
        if r_record["r_sender_interval_pkts_sent"] < 10:
            return
        if r_record["receiver_pps"] < 100:
            return

        self.receiver_pps_list.append(r_record["receiver_pps"])
        if len(self.receiver_pps_list) > 10:
            self.receiver_pps_list = self.receiver_pps_list[1:]

        receiver_pps_p90 = numpy.percentile(self.receiver_pps_list, 90)

        new_rate = int(receiver_pps_p90 * 1.2)

        if new_rate < const.UDP_MIN_RATE:
            new_rate = const.UDP_MIN_RATE
        # cap it to something big
        if new_rate > const.UDP_MAX_RATE:
            new_rate = const.UDP_MAX_RATE

        delta_rate = new_rate - self.last_new_rate

        if abs(delta_rate) < 2:
            # do not bother with tiny changes
            return

        if self.args.verbosity > 1:
            print("UdpRateManager: update: receiver pps {:6d} old rate {:6d} new rate {:6d} delta {:7d}".format(
                r_record["receiver_pps"],
                self.shared_udp_sending_rate_pps.value,
                new_rate,
                delta_rate),
                flush=True
            )

        self.shared_udp_sending_rate_pps.value = new_rate
        self.last_new_rate = new_rate
