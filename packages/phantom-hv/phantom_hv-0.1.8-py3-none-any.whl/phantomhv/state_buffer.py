"""
Provides `PhantomHVStateBuffer` which buffers register reads.
"""

import time

from .io import PhantomHVIO
from . import iostack


_ADC_TO_VOLT = 2000 / 16384
_ADC_TO_AMPERE = (2.5 / 16384) / (330e-3 * (50 / 2))


class PhantomHVStateBuffer:
    """Caches all registers of a Phantom HV crate for quick repeated access via
    the `slots` member (which contains `num_slots` `PhantomHVSlotStateBuffer`
    objects). Call `update()` after initialisation to populate the cache."""

    def __init__(self, ip, port=iostack.default_port, num_slots=1):
        self.io = PhantomHVIO(ip, port=port)
        self.num_slots = num_slots
        self.slot = [
            PhantomHVSlotStateBuffer(self, self.io, slot) for slot in range(num_slots)
        ]
        self.static_cfgs = []

    def update(self, full=False):
        """Reads all slave registers and then atomically updates the internal
        states. Any exceptions such as iostack.TimeoutError or OSError are
        passed through.

        By default (full equals False), the static configurations will only be
        read once."""

        static_cfgs, dynamic_cfgs, states = [], [], []
        for slot in range(self.num_slots):
            if slot > len(self.static_cfgs) - 1 or full:
                static_cfgs.append(self.io.read_slave_static_cfg(slot))
            else:
                static_cfgs.append(self.static_cfgs[slot])
            dynamic_cfgs.append(self.io.read_slave_dynamic_cfg(slot))
            states.append(self.io.read_slave_state(slot))

        self.last_update = time.time()
        for slot in range(self.num_slots):
            self.slot[slot].update_from(
                self.last_update, static_cfgs[slot], dynamic_cfgs[slot], states[slot]
            )

        self.static_cfgs = static_cfgs


class PhantomHVSlotStateBuffer:
    """Caches all registers of a Phantom HV module for quick repeated access via
    the `channels` member (which contains `num_channels`
    `PhantomHVChannelStateBuffer` objects). Call `update()` after initialisation
    to populate the cache.

    Setters issue synchronous requests to the hardware."""

    def __init__(self, parent, io, slot, num_channels=3):
        self.parent = parent
        self.io = io
        self.slot = slot
        self.num_channels = num_channels
        self.channel = [
            PhantomHVChannelStateBuffer(self, io, self.slot, channel)
            for channel in range(num_channels)
        ]

    def update(self, full=False):
        if not hasattr(self, "static_cfg") or full:
            static_cfg = self.io.read_slave_static_cfg(self.slot)
        else:
            static_cfg = self.static_cfg
        dynamic_cfg = self.io.read_slave_dynamic_cfg(self.slot)
        state = self.io.read_slave_state(self.slot)
        self.update_from(time.time(), static_cfg, dynamic_cfg, state)
        self.parent.update()

    def update_from(self, update_time, static_cfg, dynamic_cfg, state):
        self.last_update = update_time
        self.static_cfg = static_cfg
        self.dynamic_cfg = dynamic_cfg
        self.state = state
        for channel in self.channel:
            channel.update_from(self.last_update, static_cfg, dynamic_cfg, state)

    @property
    def hv_unlocked_ext(self):
        return bool(self.state.digital_states & 0x4)

    @property
    def hv_unlocked(self):
        return bool(self.state.digital_states & 0x1)

    @hv_unlocked.setter
    def hv_unlocked(self, unlock):
        if unlock and (self.state.digital_states & 0x4) == 0:
            raise ValueError("HV interlock error")

        cfg = self.dynamic_cfg
        with self.io.lock:
            if unlock:
                cfg.hv_enable |= 1 << 3
            else:
                cfg.hv_enable = (
                    0  # disable all HV supplies at the same time to avoid alert
                )
            self.io.write_slave_dynamic_cfg(self.slot, cfg)

    @property
    def hvs(self):
        return [self.state.adc_states[channel] * _ADC_TO_VOLT for channel in range(3)]

    @property
    def currents(self):
        return [
            self.state.adc_states[3 + channel] * _ADC_TO_AMPERE for channel in range(3)
        ]


class PhantomHVChannelStateBuffer:
    """Caches all registers of a Phantom HV channel for quick repeated access.

    Setters issue synchronous requests to the hardware."""

    def __init__(self, parent, io, slot, channel):
        self.parent = parent
        self.io = io
        self.slot = slot
        self.channel = channel

    def update(self):
        self.parent.update()

    def update_from(self, update_time, static_cfg, dynamic_cfg, state):
        self.last_update = update_time
        self.static_cfg = static_cfg
        self.dynamic_cfg = dynamic_cfg
        self.state = state

    @property
    def hv_enabled(self):
        return bool(self.dynamic_cfg.hv_enable & (1 << self.channel))

    @hv_enabled.setter
    def hv_enabled(self, enable):
        cfg = self.dynamic_cfg
        with self.io.lock:
            if enable:
                cfg.hv_enable |= 1 << self.channel
            else:
                cfg.hv_enable &= ~(1 << self.channel)
            self.io.write_slave_dynamic_cfg(self.slot, cfg)

    @property
    def hv(self) -> float:
        return self.state.adc_states[self.channel] * _ADC_TO_VOLT

    @property
    def hv_set(self):
        return self.dynamic_cfg.hv_dac[self.channel] / 2.048

    @hv_set.setter
    def hv_set(self, hv: float):
        if hv is None:
            hv = 0.0
        hv = max(0.0, min(hv, 2000.0))
        with self.io.lock:
            cfg = self.dynamic_cfg
            cfg.hv_dac[self.channel] = round(hv * 2.048)
            self.io.write_slave_dynamic_cfg(self.slot, cfg)

    @property
    def current(self):
        return self.state.adc_states[3 + self.channel] * _ADC_TO_AMPERE
