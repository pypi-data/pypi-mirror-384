#!/usr/bin/env python3
"""
Low-level control and monitoring command-line tool for Phantom HV modules.
"""

import argparse
import sys
import time

from phantomhv import PhantomHVIO, iostack


def _parse_set_dac_arg(arg):
    dac, level = map(int, arg.split(","))
    assert 0 <= dac <= 3
    assert 0 <= level <= 4095
    return dac, level


def main():
    parser = argparse.ArgumentParser("phantomhv-ctl", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("boot", help="boot application slot")
    subparsers.add_parser("reset", help="reset into bootloader")
    flash_parser = subparsers.add_parser(
        "flash",
        help="flash binary firmware image into application slot",
    )
    flash_parser.add_argument(
        "--file",
        metavar="BIN_IMAGE",
        type=argparse.FileType("rb"),
        help="firmware image to write into flash",
    )
    subparsers.add_parser("unlock-hv", help="enable HV")
    subparsers.add_parser("lock-hv", help="disable HV")
    subparsers.add_parser(
        "enable-hv",
        help="enable HV channel",
    ).add_argument(
        "channel", choices=range(3), type=int, metavar="N", help="channel to enable"
    )
    subparsers.add_parser("disable-hv", help="disable HV channel").add_argument(
        "channel", choices=range(3), type=int, metavar="N", help="channel to disable"
    )
    set_parsers = subparsers.add_parser(
        "set", help="set hardware registers"
    ).add_subparsers(dest="set", required=True)
    set_dac_parser = set_parsers.add_parser("dac")
    set_dac_parser.add_argument(
        "dac_value",
        type=_parse_set_dac_arg,
        metavar="dac,level",
        help="set output level (0-4095) of DAC (0-3)",
    )
    monitor_parser = subparsers.add_parser(
        "monitor",
        help="continuously read and print slave states",
    )
    monitor_parser.add_argument(
        "--adcs-only",
        action="store_true",
        help="continuously read and print slave ADC readings only",
    )
    monitor_parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        metavar="dt",
        help="set monitoring interval (default: 0.5 s)",
    )

    for n, p in list(subparsers.choices.items()) + list(set_parsers.choices.items()):
        if n == "set":
            continue
        p.add_argument(
            "--ip",
            metavar="HOSTNAME",
            default=iostack.default_address,
            help="IP address or hostname of the device",
        )
        p.add_argument(
            "--port", default=iostack.default_port, help="Network port of the device"
        )
        p.add_argument(
            "--slot",
            type=int,
            default=0,
            choices=range(8),
            help="destination module (hardware slot)",
        )

    args = parser.parse_args()

    io = PhantomHVIO(args.ip, port=args.port)

    if args.command == "boot":
        io.boot_app(args.slot)
    elif args.command == "reset":
        io.reset(args.slot)
    elif args.command == "flash":
        print(f"Flashing {args.ip}...")
        state_before = io.read_slave_state(args.slot)
        io.flash_app(args.file.read(), args.slot)
        state_after = io.read_slave_state(args.slot)
        if (
            state_after.spi_rx_errors != state_before.spi_rx_errors
            or state_after.spi_rx_overruns != state_before.spi_rx_overruns
        ):
            print("[ERROR] SPI communication error - please retry.")
            sys.exit(1)
    elif args.command == "unlock-hv":
        cfg = io.read_slave_dynamic_cfg(args.slot)
        cfg.hv_enable |= 1 << 3
        io.write_slave_dynamic_cfg(args.slot, cfg)
    elif args.command == "lock-hv":
        cfg = io.read_slave_dynamic_cfg(args.slot)
        cfg.hv_enable &= ~(1 << 3)
        io.write_slave_dynamic_cfg(args.slot, cfg)
    elif args.command == "disable-hv":
        cfg = io.read_slave_dynamic_cfg(args.slot)
        cfg.hv_enable &= ~(1 << args.channel)
        io.write_slave_dynamic_cfg(args.slot, cfg)
    elif args.command == "enable-hv":
        cfg = io.read_slave_dynamic_cfg(args.slot)
        cfg.hv_enable |= 1 << args.channel
        io.write_slave_dynamic_cfg(args.slot, cfg)
    elif args.command == "set" and args.set == "dac":
        dac, level = args.dac_value
        cfg = io.read_slave_dynamic_cfg(args.slot)
        cfg.hv_dac[dac] = level
        io.write_slave_dynamic_cfg(args.slot, cfg)

    if args.command == "monitor" and args.adcs_only:
        try:
            t0 = time.time()
            while True:
                t_before = time.time()
                adcs = io.read_slave_state(args.slot).adc_states
                t_after = time.time()
                print(
                    f"{t_after / 2 + t_before / 2:.3f} "
                    + " ".join(f"{adc:5.0f}" for adc in adcs)
                )
                if args.interval > 0:
                    t0 += args.interval
                    dt = t0 - time.time()
                    if dt > 0:
                        time.sleep(dt)
        except KeyboardInterrupt:
            print()
            pass
    elif args.command == "monitor":
        try:
            t0 = time.time()
            while True:
                print(io.read_slave_static_cfg(args.slot), end=" ")
                print(io.read_slave_dynamic_cfg(args.slot), end=" ")
                print(io.read_slave_state(args.slot), flush=True)

                t0 += args.interval
                dt = t0 - time.time()
                if dt > 0:
                    time.sleep(dt)
        except KeyboardInterrupt:
            print()
            pass
