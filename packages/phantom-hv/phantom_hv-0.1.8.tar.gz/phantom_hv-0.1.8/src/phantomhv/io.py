"""
Provides the class `PhantomHVIO` for low-level I/O.
"""

import struct
import threading
import time

from . import iostack


class PhantomHVSlaveStaticCfg:
    def __init__(self, buf):
        self.fw_rev, self.hw_rev, self.bl_rc, self.hw_uid = struct.unpack("<HHHQ", buf)

    def __str__(self):
        return str(self.__dict__)

    @staticmethod
    def size():
        return 14


class PhantomHVSlaveDynamicCfg:
    def __init__(self, buf):
        self.hv_enable, self.led_enable, self.pulse_enable = struct.unpack(
            "<" + "H" * 3, buf[:6]
        )
        self.hv_dac = list(struct.unpack("<" + "H" * 4, buf[6:14]))
        self.offset_dac = list(struct.unpack("<" + "H" * 4, buf[14:]))

    def pack(self):
        return struct.pack(
            "<" + "H" * 11,
            self.hv_enable,
            self.led_enable,
            self.pulse_enable,
            *self.hv_dac,
            *self.offset_dac
        )

    def __str__(self):
        return str(self.__dict__)

    @staticmethod
    def size():
        return 22


class PhantomHVSlaveState:
    def __init__(self, buf):
        self.status, self.spi_rx_errors, self.spi_rx_overruns, self.digital_states = (
            struct.unpack("<HHHH", buf[:8])
        )
        self.adc_states = list(struct.unpack("<" + "h" * 8, buf[8:24]))
        self.alerts, self.warnings, self.ticks = struct.unpack("<HHH", buf[24:])

    def __str__(self):
        return str(self.__dict__)

    @staticmethod
    def size():
        return 30


class PhantomHVIO(iostack.IOStack):
    PHANTOM_HV_MASTER_SUBSYSTEM = 0x11
    PHANTOM_HV_MASTER_CMD_SPI_IO_REQUEST = 0x0

    def __init__(
        self,
        ip,
        port=iostack.default_port,
        timeout=iostack.default_timeout,
        max_retries=iostack.default_retries,
        verbosity=iostack.default_verbosity,
        max_packet_size=iostack.default_max_packet_size,
        interface_ip=None,
    ):
        """Connects to the SPI I/O subsystem at the given address.

        Parameters
        ----------
        ip : string
            Destination address.
        port : int, optional
            Destination port (default: 512).
        timeout : float, optional
            Response timeout in seconds (default: 200 ms).
        verbosity : int, optional
            Verbosity level (default: 0, silent)
        max_packet_size : int, optional
            Expected maximum size of replies (default: 256 Bytes).
        interface_ip : str, optional
            IP address of local interface (default: let OS choose).
        """
        iostack.IOStack.__init__(
            self,
            ip=ip,
            port=port,
            timeout=timeout,
            max_retries=max_retries,
            verbosity=verbosity,
            max_packet_size=max_packet_size,
            interface_ip=interface_ip,
        )
        self.lock = threading.RLock()

    def _transfer(self, buffer):
        """Transmits the contents of buffer via SPI and returns the (same number of) bytes received."""
        with self.lock:
            return self.request(
                PhantomHVIO.PHANTOM_HV_MASTER_SUBSYSTEM,
                PhantomHVIO.PHANTOM_HV_MASTER_CMD_SPI_IO_REQUEST,
                buffer,
            )

    def _read_register(self, slot, register: int, Factory):
        assert register in (0, 1, 2)
        assert slot in range(8)
        with self.lock:
            response = self.request(
                PhantomHVIO.PHANTOM_HV_MASTER_SUBSYSTEM,
                PhantomHVIO.PHANTOM_HV_MASTER_CMD_SPI_IO_REQUEST,
                bytearray([slot, (1 << 4) | register, 0] + [0] * Factory.size()),
            )
        assert len(response.payload) == Factory.size() + 2
        return Factory(response.payload[2:])

    def read_slave_static_cfg(self, slot):
        assert slot in range(8)
        with self.lock:
            return self._read_register(slot, 0, PhantomHVSlaveStaticCfg)

    def read_slave_dynamic_cfg(self, slot):
        assert slot in range(8)
        with self.lock:
            return self._read_register(slot, 1, PhantomHVSlaveDynamicCfg)

    def read_slave_state(self, slot):
        assert slot in range(8)
        with self.lock:
            return self._read_register(slot, 2, PhantomHVSlaveState)

    def write_slave_dynamic_cfg(self, slot, cfg):
        assert slot in range(8)
        with self.lock:
            self.request(
                PhantomHVIO.PHANTOM_HV_MASTER_SUBSYSTEM,
                PhantomHVIO.PHANTOM_HV_MASTER_CMD_SPI_IO_REQUEST,
                bytearray([slot, 0x21]) + cfg.pack(),
            )

    def _write_page(self, page: int, data: str, slot: int, min_timeout=0.5):
        assert 0 <= slot <= 8
        assert len(data) <= 256
        assert page >= 0 and page < 4096
        header = struct.pack("<BBB", slot, (3 << 4) | (page >> 8) & 0xF, page & 0xFF)
        pad = b"\x00" * (256 - len(data))

        with self.lock:
            # Increase timeout if needed
            old_timeout = self.get_timeout()
            if old_timeout < min_timeout:
                self.set_timeout(min_timeout)

            self.request(
                PhantomHVIO.PHANTOM_HV_MASTER_SUBSYSTEM,
                PhantomHVIO.PHANTOM_HV_MASTER_CMD_SPI_IO_REQUEST,
                header + data + pad,
            )

            # Restore old timeout
            if old_timeout < min_timeout:
                self.set_timeout(old_timeout)

    def flash_app(self, data: str, slot: int, sleep_interval=0.1):
        print("Flashing", end="", flush=True)
        with self.lock:
            for i in range((len(data) - 1) // 256 + 1):
                print(".", end="", flush=True)
                page = data[i * 256 : (i + 1) * 256]
                self._write_page(i, page, slot)
                if sleep_interval > 0:
                    time.sleep(sleep_interval)
            print()

    def boot_app(self, slot: int):
        with self.lock:
            self.request(
                PhantomHVIO.PHANTOM_HV_MASTER_SUBSYSTEM,
                PhantomHVIO.PHANTOM_HV_MASTER_CMD_SPI_IO_REQUEST,
                bytearray([slot, 0x50]),
            )

    def reset(self, slot: int):
        with self.lock:
            self.request(
                PhantomHVIO.PHANTOM_HV_MASTER_SUBSYSTEM,
                PhantomHVIO.PHANTOM_HV_MASTER_CMD_SPI_IO_REQUEST,
                bytearray([slot, 0x60]),
            )
