# Copyright (c) 2024 Cloudflare, Inc.
# Licensed under the Apache 2.0 license found in the LICENSE file or at https://www.apache.org/licenses/LICENSE-2.0

import time

from . import udp_helper


# falling off the end of this method terminates the process
def run(readyevent, doneevent, args, data_sock, peer_addr, string_to_send):
    if args.verbosity:
        print("udp string sender thread: start of process", flush=True)

    ping_interval_sec = 0.2
    ping_duration_sec = 5
    total_pings_to_send = ping_duration_sec / ping_interval_sec

    send_count = 0

    readyevent.set()

    while True:
        if doneevent.is_set():
            break

        udp_helper.sendto(data_sock, peer_addr, string_to_send.encode())
        send_count += 1

        time.sleep(ping_interval_sec)

        if send_count > total_pings_to_send:
            break

    if args.verbosity:
        print("udp string sender thread: end of process", flush=True)
