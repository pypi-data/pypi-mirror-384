#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base interface to the I/O stack running on the GECCO platform
Subsystems should be derived from the IOStack class.
"""

from __future__ import print_function
from builtins import range

import collections
import random
import socket
import struct
import enum
import json
import sys
import binascii
import time

default_address = "192.168.1.115"
default_port = 512
default_timeout = 0.3
default_retries = 3
default_verbosity = 0
default_max_packet_size = 300

SYS_IOSTACK = 0

class Command(object):
    """I/O stack command codes."""
    CMD_READ_REG = 0
    CMD_WRITE_REG = 1
    CMD_PING = 2
    CMD_APP_RESET = 3
    CMD_BOOT_RESET = 4
    CMD_FLASH_START = 5
    CMD_FLASH_WRITE_PAGE = 6
    CMD_FLASH_FINISH = 7
    CMD_CLEAR_BOOTPROT = 100
    CMD_FLASH_BOOT_START = 101
    CMD_FLASH_BOOT_WRITE_PAGE = 102
    CMD_FLASH_BOOT_FINISH = 103
    CMD_REPORT_ERR = 65525


class Register(object):
    """I/O stack registers."""
    REG_ETHERNET_CFG = 0
    REG_IDS = 1
    REG_BOOT_OPT = 2


class Status(object):
    """I/O stack error codes."""
    ERR_OKAY = 0
    ERR_UNKNOWN_SUBSYSTEM = 1
    ERR_UNKNOWN_COMMAND = 2
    ERR_INVALID_SIZE = 3
    ERR_INVALID_REGISTER = 4
    ERR_INVALID_MAC = 5
    ERR_UNHANDLED_ERROR = 6

class BootOptFlags(enum.IntFlag):
    AUTOSTART = 0x1
    CHECKCRC  = 0x2
    SETBOOTPROT = 0x4
    APPWATCHDOG = 0x8

# Generate lookup maps
for c in Register,Command, Status:
    c.lookup = {v: k for (k, v) in c.__dict__.items()
                if not k.startswith('__')}


class Error(Exception):
    """Base exception in case we need extended functionality in the future."""
    pass


class TimeoutError(Error):
    """Timeout occured while waiting for a response."""
    pass


class ResponseError(Error):
    """Received a malformed response."""
    pass


class RequestError(Error):
    """Reply indicated an invalid request."""
    pass


Response = collections.namedtuple("Response",
                                  "id subsystem_id response_code "
                                  "payload")

SubsystemResponse = collections.namedtuple("SubsystemResponse",
                                           "response_code payload")

IOStackConfig = collections.namedtuple("IOStackConfig",
                                       "ip subnet gateway mac")

IOStackIDs = collections.namedtuple("IOStackIDs",
                                       "serial EUI48 HWrev FWrev")

IOStackBootOpt = collections.namedtuple("IOStackBootOpt",
                                        "flags delay size CRC")

class IOStack(object):
    def __init__(self, ip, port=default_port, timeout=default_timeout,
                 max_retries=default_retries, verbosity=default_verbosity,
                 max_packet_size=default_max_packet_size,
                 interface_ip=None):
        """Connects to an I/O stack with the given address.

        Parameters
        ----------
        ip : string
            Destination address.
        port : int, optional
            Destination port (default: 512).
        timeout : float, optional
            Response timeout in seconds (default: 200 ms).
        max_retries : int, optional
            Maximum number of retries after a timeout (default: 3).
        verbosity : int, optional
            Verbosity level (default: 0, silent)
        max_packet_size : int, optional
            Expected maximum size of replies (default: 256 Bytes).
        interface_ip : str, optional
            IP address of local interface (default: let OS choose).
        """

        self.verbosity = verbosity
        self.max_packet_size = max_packet_size
        self.request_id = random.randint(0, 65535)
        self.max_retries = max_retries

        # Connect
        self.cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if interface_ip is not None:
            # Bind to a specific interface
            for local_port in range(1025, 65535):
                try:
                    self.cs.bind((interface_ip, local_port))
                    if self.verbosity:
                        print("IOStack: bound to %s:%i" % (interface_ip, local_port), file=sys.stderr)
                    break
                except:
                    pass
            else:
                raise RuntimeError("error: no free UDP port on interface with IP %s" % interface_ip)

            self.cs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.cs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.cs.connect((ip, port))
        self.cs.settimeout(timeout)
        if self.verbosity:
            print("IOStack: opened connection to %s:%i, %.0f ms timeout" % (ip, port, 1000 * timeout), file=sys.stderr)

    def __del__(self):
        """Disconnects from an I/O stack"""
        self.cs.close()

    def set_timeout(self, timeout):
        self.cs.settimeout(timeout)

    def get_timeout(self):
        return self.cs.gettimeout()

    def multi_request(self, subsystem_id, request_code, payload, broadcast=False,
                      max_retries=None):
        """
        Send a request and yield one or more replies.

        Parameters
        ----------
        subsystem_id : int
            Identifier of the target subsystem.
        request_code : int
            Identifier of the command to execute.
        payload : bytearray or string
            Payload to append to the request.
        broadcast : bool, optional
            If true, wait for multiple answers (default: False).
        max_retries : int, optional
            Maximum number of retries after a timeout (None: use default
            value).

        Yields
        ------
        Response
            Responses with raw payload.
        """
        # Pack and transmit request
        self.request_id = (self.request_id + 1) % 65536
        request = struct.pack("<HBH", self.request_id, subsystem_id,
                              request_code) + payload

        self.cs.send(request)

        # Receive response
        trials_left = self.max_retries if max_retries is None else int(max_retries)
        while True:
            try:
                reply = self.cs.recv(self.max_packet_size)
            except socket.timeout:
                if trials_left > 0:  # Retry
                    trials_left -= 1
                    self.cs.send(request)
                    continue

                raise TimeoutError("network error: request timed out")

            if len(reply) < 5:
                raise ResponseError("response too short")

            header, payload = reply[:5], reply[5:]
            response = Response(*struct.unpack("<HBH", header),
                                payload=payload)

            if response.id != self.request_id:
                if self.verbosity:
                    print("skipping packet %s" % str(response), file=sys.stderr)

                continue

            # Perform sanity checks
            if response.subsystem_id == 0:
                if response.response_code not in Command.lookup:
                    raise ResponseError("invalid response code %i" % response.response_code)

                if response.response_code == Command.CMD_REPORT_ERR:
                    if len(response.payload) != 2:
                        raise ResponseError("invalid error size %i" % len(response.payload))

                    error_code, = struct.unpack("<H", response.payload)
                    if error_code not in Status.lookup:
                        raise ResponseError("invalid error code %i" % error_code)

                    raise RequestError(Status.lookup[error_code])

            if response.subsystem_id != subsystem_id:
                raise ResponseError("invalid subsystem id %i" % response.subsystem_id)

            yield response

            if not broadcast:
                break

    def request(self, subsystem_id, request_code, payload, max_retries=None):
        """Send a request and return the response.

        Parameters
        ----------
        subsystem_id : int
            Identifier of the target subsystem.
        request_code : int
            Identifier of the command to execute.
        payload : bytearray or string
            Payload to append to the request.
        max_retries : int, optional
            Maximum number of retries after a timeout (None: use default
            value).

        Returns
        -------
        Response
            Response with raw payload.
        """
        return list(self.multi_request(subsystem_id, request_code, payload,
                    False, max_retries=max_retries))[0]

    def multiread_register(self, register, type_code="<H", max_retries=None):
        """Read from a register from multiple devices and yield their contents.

        Parameters
        ----------
        register : int
            The register to read from.
        type_code : str
            The format of the response payload (see the documentation of Python's
            struct module).
        max_retries : int, optional
            Maximum number of retries after a timeout (None: use default
            value).

        Yields
        ------
        SubsystemResponse
            Response with payload decoded according to the type_code parameter.
        """
        payload = struct.pack("<H", register)

        for response in self.multi_request(SYS_IOSTACK, Command.CMD_READ_REG,
                                           payload, broadcast=True,
                                           max_retries=max_retries):
            yield SubsystemResponse(response.response_code,
                                    struct.unpack(type_code, response.payload))

    def read_register(self, register, type_code="<H", max_retries=None):
        """Reads from a register and returns its content.

        Parameters
        ----------
        register : int
            The register to read from.
        type_code : string
            The format of the response payload (see the documentation of Python's
            struct module).
        max_retries : int, optional
            Maximum number of retries after a timeout (None: use default
            value).

        Returns
        -------
        SubsystemResponse
            Response with payload decoded according to the type_code parameter.
        """
        payload = struct.pack("<H", register)

        response = self.request(SYS_IOSTACK, Command.CMD_READ_REG, payload,
                                max_retries=max_retries)

        return SubsystemResponse(response.response_code,
                                 struct.unpack(type_code, response.payload))

    def write_register(self, register, value, type_code="<H", max_retries=None):
        """Writes to a register.

        Parameters
        ----------
        register : int
            The register to write to.
        value : int, bytearray or str
            The value to write to the register. If typecode is not None, the
            value is first encoded with struct.pack using the given format.
        type_code : str
            The format of value (see the documentation of Python's struct
            module). If None, value is assumed to be a bytearray or string
            which will not be encoded.
        max_retries : int, optional
            Maximum number of retries after a timeout (None: use default
            value).
        """
        payload = struct.pack("<H", register)
        if type_code:  # pack value according to type code
            payload += struct.pack(type_code, *value)
        else:  # transparently pass value
            payload += value

        response = self.request(SYS_IOSTACK, Command.CMD_WRITE_REG, payload,
                                max_retries=max_retries)

        return response.response_code

    def ping(self, payload=None):
        """Probes the connection to the device by sending a random payload."""
        header_size = 5
        if payload is None:
            payload = bytearray(random.randint(0, 255)
                                for i in range(64 - header_size))
        elif len(payload) > self.max_packet_size - header_size:
            payload = payload[:self.max_packet_size - header_size]

        response = self.request(SYS_IOSTACK, Command.CMD_PING, payload, max_retries=0)
        if response.payload != payload:
            raise ResponseError("payload mismatch")
        return payload

    def reset(self):
        """Requests a SW reset of the device."""
        response = self.request(SYS_IOSTACK,Command.CMD_APP_RESET, b"")

    def boot_reset(self):
        """Requests a reset to the bootloader"""
        response = self.request(SYS_IOSTACK,Command.CMD_BOOT_RESET, b"")

    def get_config(self):
        """Reads the configuration of the device."""
        response = self.request(SYS_IOSTACK,Command.CMD_READ_REG,
                                struct.pack("<H",Register.REG_ETHERNET_CFG))
        config = IOStackConfig(".".join("%d" % m for m in bytes(response.payload[14:18])),
                               ".".join("%d" % m for m in bytes(response.payload[4:8])),
                               ".".join("%d" % m for m in bytes(response.payload[0:4])),
                               ":".join("%02X" % m for m in bytes(response.payload[8:14])))
        return config

    def set_config(self, ip=None, subnet=None, gateway=None, mac=None):
        """Writes the configuration of the device."""
        old_config=self.get_config()
        if ip is None:
            ip=old_config.ip
        if subnet is None:
            subnet=old_config.subnet
        if gateway is None:
            gateway=old_config.gateway
        if mac is None:
            mac=old_config.mac

        if len(ip.split('.')) != 4:
            raise Error("Invalid config")
        if len(subnet.split('.')) != 4:
            raise Error("Invalid config")
        if len(gateway.split('.')) != 4:
            raise Error("Invalid config")
        if len(mac.split(':')) != 6:
            raise Error("Invalid config")

        payload = bytes(map(int,gateway.split('.'))) + \
                  bytes(map(int,subnet.split('.'))) + \
                  bytes([int(x,16) for x in mac.split(':')]) + \
                  bytes(map(int,ip.split('.')))

        response = self.request(SYS_IOSTACK,Command.CMD_WRITE_REG,
                                struct.pack("<H",Register.REG_ETHERNET_CFG) + \
                                payload);

    def get_boot_opt(self):
        """Reads the boot options of the device."""
        response = self.request(SYS_IOSTACK,Command.CMD_READ_REG,
                                struct.pack("<H",Register.REG_BOOT_OPT))
        boot_opt = IOStackBootOpt(BootOptFlags(struct.unpack("<L",response.payload[0:4])[0]),
                                  struct.unpack("<L",response.payload[4:8])[0],
                                  struct.unpack("<L",response.payload[8:12])[0],
                                  "0x{:08X}".format(struct.unpack("<L",response.payload[12:16])[0]))
        return boot_opt

    def set_boot_opt(self,flags=None,delay=None):
        """Writes the boot options of the device."""
        old_boot_opt=self.get_boot_opt()
        if flags is None:
            flags=old_boot_opt.flags
        if delay is None:
            delay=old_boot_opt.delay

        payload = bytes(struct.pack("<L",int(flags))+
                        struct.pack("<L",int(delay))+
                        struct.pack("<L",int(old_boot_opt.size))+
                        struct.pack("<L",int(old_boot_opt.CRC,16)))
        response = self.request(SYS_IOSTACK,Command.CMD_WRITE_REG,
                                struct.pack("<H",Register.REG_BOOT_OPT) + \
                                payload);

    def get_IDs(self):
        """Reads the IDs of the device (serials, FW/HW revisions)."""
        response = self.request(SYS_IOSTACK,Command.CMD_READ_REG,
                                struct.pack("<H",Register.REG_IDS))
        config = IOStackIDs(":".join("%02X" % m for m in bytes(response.payload[0:16])),
                            ":".join("%02X" % m for m in bytes(response.payload[16:22])),
                            int(response.payload[22]),
                            response.payload[23:].decode())
        return config

    def clear_bootprot(self):
        """
        Clears the BOOTPROT so a new bootloader can be flashed
        A reboot is needed to be effective
        Also the SETBOOTPROT option should be disabled beforehand
        """
        response = self.request(SYS_IOSTACK,Command.CMD_CLEAR_BOOTPROT, b"")


    def upload_FW(self,fdata):
        """Uploads a new version of the FW into the system!"""
        padlen=((len(fdata)-1)//256+1)*256-(len(fdata))
        size=len(fdata)+padlen
        pad = b'\xFF' * padlen
        data=fdata+pad
        crc=0
        crc=binascii.crc32(data,crc)

        response = self.request(SYS_IOSTACK,Command.CMD_FLASH_START,
                                struct.pack("<LL",size,crc))

        print("Uploading FW with size {} bytes (padded) and CRC code 0x{:08X}".format(size,crc))

        for i in range((len(data) - 1) // 256 + 1):
            page = data[i * 256:(i + 1) * 256]
            print (".",end="",flush=True)
            header = struct.pack("<H",i)
            response = self.request(SYS_IOSTACK,Command.CMD_FLASH_WRITE_PAGE,
                                    header+page)

        print ("")
        print("Finishing FW Upload")
        response = self.request(SYS_IOSTACK,Command.CMD_FLASH_FINISH,b"")

    def upload_boot_FW(self,fdata):
        """
        Uploads a new version of the bootloader FW into the system!
        Only possible if running in the main Application FW (if it supports this feature)
        """
        padlen=((len(fdata)-1)//256+1)*256-(len(fdata))
        size=len(fdata)+padlen
        pad = b'\xFF' * padlen
        data=fdata+pad

        if size>65535:
            print("Bootloader FW too big. Aborting.")
            return

        response = self.request(SYS_IOSTACK,Command.CMD_FLASH_BOOT_START,
                                struct.pack("<L",size))

        print("Uploading Bootloader FW with size {} bytes (padded)".format(size))

        for i in range((len(data) - 1) // 256 + 1):
            page = data[i * 256:(i + 1) * 256]
            print (".",end="",flush=True)
            header = struct.pack("<H",i)
            response = self.request(SYS_IOSTACK,Command.CMD_FLASH_BOOT_WRITE_PAGE,
                                    header+page)

        print ("")
        print("Finishing FW Upload")
        response = self.request(SYS_IOSTACK,Command.CMD_FLASH_BOOT_FINISH,b"")

# allow to use this as an standalone test program
if __name__ == "__main__":
    import argparse

    def try_to_exec(expression,times=10):
        for attempt in range(times):
            try:
                exec(expression)
                break
            except:
                print (".",end="",flush=True)
                pass
            time.sleep(1)
        else:
            print (" Failed")
            return False
        print (" Success")
        return True

    # Parse command-line arguments
    arg_epilog="""Bootloader flags:
{}
""".format(json.dumps({i.name:i.value for i in BootOptFlags},indent=2))

    """
    {}
    Status Register Bits:
    {}
    ADC Channels:
    {}
    DAC Commands:
    {}
    DAC Channels:
    {}
    .format(json.dumps({i.name:i.value for i in Register},indent=2),
               json.dumps({i.name:i.value for i in StatusBits},indent=2),
               json.dumps({i.name:i.value for i in ADCAddress},indent=2),
               json.dumps({i.name:i.value for i in DACCommand},indent=2),
               json.dumps({i.name:i.value for i in DACAddress},indent=2),
               )
    """


    parser = argparse.ArgumentParser(
        description="Issue commands to the iostack subsystem of a GECCO board",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=arg_epilog)
    parser.add_argument("-i", "--ip", type=str, default=default_address,
                        help="IP address of the device (default: %s)" % default_address)
    parser.add_argument("-p","--port", type=int, default=default_port,
                        help="port (default: %i)" % default_port)
    parser.add_argument("-s","--string", type=str,
                        help="String used for pinging")
    parser.add_argument("-r","--reset", action='store_true',
                        help = "Request a reset")
    parser.add_argument("-b","--boot_reset", action='store_true',
                        help = "Request a reset to bootloader")
    parser.add_argument("-f","--force", action='store_true',
                        help = "Force command without trying to reset to bootloader")
    parser.add_argument("--get_config", action='store_true',
                        help = "Get target configuration")
    parser.add_argument("--get_boot_opt", action='store_true',
                        help = "Get target boot options")
    parser.add_argument("--get_IDs", action='store_true',
                        help = "Get target IDs")
    parser.add_argument("--ping", action='store_true',
                        help = "ping target")
    parser.add_argument("--set_ip", type=str,
                        help = "Set target IP address")
    parser.add_argument("--set_subnet", type=str,
                        help = "Set target subnet mask")
    parser.add_argument("--set_gateway", type=str,
                        help = "Set target gateway address")
    parser.add_argument("--set_boot_flags", type=str,
                        help = "Set bootloader flags")
    parser.add_argument("--set_boot_delay", type=int,
                        help = "Set bootloader delay (in ms, negative for infinite wait)")
    parser.add_argument("--fw_upload", type=str,
                        help = "Upload a new FW")
    parser.add_argument("--boot_fw_upload", type=str,
                        help = "Upload a new FW for the bootloader")
    parser.add_argument("--clear_bootprot", action='store_true',
                        help = "Clear the BOOTPROT protection of the bootloader")

    args = parser.parse_args()

    target=IOStack(ip=args.ip,port=args.port)

    if (args.fw_upload!=None):
        raw_data = open(args.fw_upload, 'rb').read()
        print("Requesting reset into bootloader")
        if (args.force or try_to_exec("target.boot_reset()")):
            print("Initiate FW upload")
            try_to_exec("target.upload_FW(raw_data)")

    if (args.boot_fw_upload!=None):
        raw_data = open(args.boot_fw_upload, 'rb').read()
        print("Initiate FW upload")
        try_to_exec("target.upload_boot_FW(raw_data)")

    if ((args.set_ip!=None) or
        (args.set_subnet!=None) or
        (args.set_gateway!=None)):
        if args.set_ip!=None:
            print ("Setting IP:{}".format(args.set_ip))
        if args.set_subnet!=None:
            print ("Setting subnet mask:{}".format(args.set_subnet))
        if args.set_gateway!=None:
            print ("Setting gateway:{}".format(args.set_gateway))
        input("Press Enter to confirm...")

        print("Requesting reset into bootloader")
        if (args.force or try_to_exec("target.boot_reset()")):
            print("Setting Ethernet configuration")
            try_to_exec("target.set_config(ip=args.set_ip,subnet=args.set_subnet,gateway=args.set_gateway)")
        exit()

    if ((args.set_boot_flags!=None) or
        (args.set_boot_delay!=None)):
        flags=args.set_boot_flags
        if args.set_boot_flags!=None:
            if args.set_boot_flags.isnumeric():
                flags=BootOptFlags(int(args.set_boot_flags))
            else:
                flags=BootOptFlags(0)
                for i in args.set_boot_flags.split("|"):
                    flags|=BootOptFlags[i]
            print ("Setting Bootloader flags:{}".format(flags))
        if args.set_boot_delay!=None:
            if (args.set_boot_delay<0):
                args.set_boot_delay= 0xFFFFFFFF
            print ("Setting Bootloader delay:{} ms".format(args.set_boot_delay))
        input("Press Enter to confirm...")

        print("Requesting reset into bootloader")
        if (args.force or try_to_exec("target.boot_reset()")):
            print("Setting Bootloader options")
            try_to_exec("target.set_boot_opt(flags=flags,delay=args.set_boot_delay)")
        exit()

    if args.reset:
        target.reset()

    if args.boot_reset:
        target.boot_reset()

    if args.clear_bootprot:
        target.clear_bootprot()

    if args.get_IDs:
        print(target.get_IDs())

    if args.get_config:
        print(target.get_config())

    if args.get_boot_opt:
        print(target.get_boot_opt())

    if args.ping:
        if (args.string!=None):
            print("Using the following string as payload: {}".format(args.string))
            print("Received the this reply from target:   {}".format(
                target.ping(bytes(args.string.encode('utf-8'))).decode('utf-8')))
        else:
            print("Using a random payload")
            target.ping(args.string)
            print("Done")
