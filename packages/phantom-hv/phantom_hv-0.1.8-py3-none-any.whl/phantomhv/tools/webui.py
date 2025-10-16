#!/usr/bin/env python3
"""
Web UI to monitor and control a Phantom HV crate.
"""

import argparse

from phantomhv import iostack
from phantomhv.webui_components import PhantomHVWebUI


def parse_host_port(s, default_host=None, default_port=None):
    if ":" in s:
        if s.startswith(":"):
            return default_host, int(s[1:])
        else:
            host, port = s.split(":")
            return host, int(port)

    return s, default_port


def main():
    parser = argparse.ArgumentParser("phantomhv-webui", description=__doc__)
    parser.add_argument(
        "--address",
        default=f"{iostack.default_address}:{iostack.default_port}",
        required=False,
        type=lambda s: parse_host_port(s, default_port=iostack.default_port),
        metavar="ip:port",
        help=f"IP address or hostname of the device (default: {iostack.default_address}:{iostack.default_port})",
    )
    parser.add_argument(
        "--num-slots",
        default=1,
        type=int,
        choices=range(1, 9),
        help="number of modules to display (default: 1)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--show",
        default=False,
        action="store_true",
        help="open UI in native window",
    )
    group.add_argument(
        "--bind",
        default=("127.0.0.1", 8080),
        type=lambda s: parse_host_port(s, default_host="127.0.0.1", default_port=8080),
        metavar="host:port",
        help="bind web server to a specific network interface/port (default: 127.0.0.1:8080; use 0.0.0.0 to bind to all interfaces)",
    )

    args = parser.parse_args()
    hv_host, hv_port = args.address
    bind_host, bind_port = args.bind

    web_ui = PhantomHVWebUI(hv_host, hv_port, num_slots=args.num_slots)

    try:
        web_ui.run(show=args.show, bind_host=bind_host, bind_port=bind_port)
    except KeyboardInterrupt:
        print()
        print("caught ctrl+c; shutting down")
