"""
Components for the Web UI.
"""

import collections
import time
import types

try:
    from importlib.resources import files
except ImportError:  # Python <3.9
    from importlib_resources import files

from nicegui import app, ui, run, elements
import numpy as np
import plotly.graph_objects as go

from phantomhv import iostack, state_buffer


def get_hv_setter(
    channel_state: state_buffer.PhantomHVChannelStateBuffer,
    channel_hv_set: elements.number.Number,
):
    """Returns a function that sets the channel's HV to `channel_hv_set`'s
    value.

    The function then retrieves the actual DAC value that has been programmed
    and updates the spinbox accordingly.
    """

    def set_hv():
        channel_state.hv_set = channel_hv_set.value
        channel_state.update()
        channel_hv_set.value = round(channel_state.hv_set)

    return set_hv


def get_hv_timeseries_updater(
    slot: state_buffer.PhantomHVSlotStateBuffer, duration_sec=65
):
    """Returns a function that on each call puts the latest voltage measurements
    of the given module slot into a ring buffer of `duration_sec` seconds
    length, and returns these measurements as a tuple of (numpy datetime64
    timestamps, voltages/V 2d array)."""
    t, v = collections.deque(), collections.deque()

    def get_hv_timeseries():
        time_ms = round(slot.last_update * 1000)
        voltages = slot.hvs

        if len(t) == 0 or time_ms > t[-1]:
            t.append(time_ms)
            v.append(voltages)

            while (t[-1] - t[0]) / 1000 > duration_sec:
                t.popleft()
                v.popleft()

        return np.array(t, dtype="datetime64[ms]"), np.array(v)

    return get_hv_timeseries


def get_current_timeseries_updater(
    slot: state_buffer.PhantomHVSlotStateBuffer, duration_sec=65
):
    """Returns a function that on each call puts the latest current measurements
    of the given module slot into a ring buffer of `duration_sec` seconds
    length, and returns these measurements as a tuple of (numpy datetime64
    timestamps, currents/mA 2d array)."""
    t, i = collections.deque(), collections.deque()

    def get_current_timeseries():
        time_ms = round(slot.last_update * 1000)
        currents = slot.currents

        if len(t) == 0 or time_ms > t[-1]:
            t.append(time_ms)
            i.append(currents)

            while (t[-1] - t[0]) / 1000 > duration_sec:
                t.popleft()
                i.popleft()

        return np.array(t, dtype="datetime64[ms]"), 1000.0 * np.array(i)

    return get_current_timeseries


class PhantomHVWebUI:
    _header_font_classes = "font-medium text-purple-600"

    def __init__(
        self, host, port=iostack.default_port, num_slots=1, update_interval=0.2, log_interval=1.0,
    ):
        self.host = host
        self.port = port
        self.num_slots = num_slots
        self.default_update_interval = update_interval
        self.timeout_notification = None
        self.update_time = None
        self.num_failures = 0
        self.update_timer = None
        self.log_interval = log_interval
        if self.log_interval > 0.0:
            self.log_time = time.time()
        else:
            self.log_time = float("inf")

        self.hv_state = state_buffer.PhantomHVStateBuffer(
            host, port=port, num_slots=num_slots
        )
        self.hv_timeseries = []
        self.current_timeseries = []

    def run(self, show=False, bind_host=None, bind_port=None):
        self.init_ui()

        run_args = {
            "title": "Phantom HV Web UI",
            "dark": True,
            "reload": False,
            "show": show,
            "native": show,
            "show_welcome_message": False,
        }

        if show:
            run_args["window_size"] = (1200, 130 + 160 * self.num_slots)
        else:
            run_args["host"] = bind_host
            run_args["port"] = bind_port

        ui.run(**run_args)

    def on_exception(self, error):
        ui.notify(error)

    def init_ui(self):
        ui.query("body").style(
            "font-family: 'Source Code Pro', 'Source Code Variable', Courier, monospace"
        ).classes("text-lg")

        ui.switch.default_props("color=deep-purple")
        ui.label(f"Phantom HV Web UI [{self.host}:{self.port}]").classes(
            self._header_font_classes
        )

        app.add_static_files(
            "/woff2", files("phantomhv") / "resources" / "woff2"
        )
        ui.add_head_html(
            r"""
        <style>
        @font-face{
            font-family: 'Source Code Variable';
            font-weight: 200 900;
            font-style: normal;
            font-stretch: normal;
            font-display: swap;
            src: url('/woff2/SourceCodeVF-Upright.otf.woff2') format('woff2');
        }
        </style>
        """
        )
        app.on_exception(self.on_exception)
        self.update_timer = ui.timer(0, self.update_state, once=True)

    def build_ui(self):
        with ui.grid(columns=10 * "auto " + "1fr").classes(
            "w-full items-baseline text-center gap-y-0"
        ):
            # Setup header row
            ui.label.default_classes(self._header_font_classes)
            ui.label("Slot")
            ui.label("Interlock")
            ui.label("HV unlock")
            ui.label("Channel")
            ui.label("HV enable")
            ui.label("Set voltage").classes("col-span-2")
            ui.label("Voltage")
            ui.label("Current")
            ui.label("History").classes("text-left col-span-2")
            ui.label.default_classes(remove=self._header_font_classes)

            for slot in range(self.num_slots):
                slot_state = self.hv_state.slot[slot]
                for channel in range(3):
                    # Setup one row per channel
                    channel_state = slot_state.channel[channel]
                    if channel == 0:
                        # Slot (spans 3 rows)
                        ui.label(f"{slot}").classes("row-span-3")

                        # Interlock (spans 3 rows)
                        ui.label("ok").classes(
                            "row-span-3 text-emerald-500 font-medium"
                        ).bind_visibility_from(slot_state, "hv_unlocked_ext")
                        ui.label("error").classes(
                            "row-span-3 text-rose-500 font-medium"
                        ).bind_visibility_from(
                            slot_state, "hv_unlocked_ext", lambda b: not b
                        )

                        # HV unlock (cannot span multiple rows because of alignment issues)
                        # We can only toggle HV unlock if the interlock is 'ok'.
                        slot_hv_enable = (
                            ui.switch()
                            .bind_value(slot_state, "hv_unlocked")
                            .bind_enabled_from(slot_state, "hv_unlocked_ext")
                        ).classes("place-self-center")
                        slot_hv_enable._props["loopback"] = False  # nicer UX
                    else:
                        # HV unlock
                        ui.label("")

                    # Channel
                    ui.label(f"{channel}")

                    # HV enable
                    channel_hv_enable = (
                        ui.switch()
                        .bind_value(channel_state, "hv_enabled")
                        .bind_enabled_from(slot_hv_enable, "value")
                        .classes("place-self-center")
                    )
                    channel_hv_enable._props["loopback"] = False  # nicer UX

                    # Set voltage
                    channel_hv_set = (
                        ui.number(
                            "",
                            min=0,
                            max=2000,
                            precision=0,
                            value=round(channel_state.hv_set),
                        )
                        .bind_enabled_from(channel_hv_enable, "value")
                        .props("dense suffix='V' size='xl'")
                    )
                    ui.button(
                        "set",
                        color="deep-purple",
                        on_click=get_hv_setter(channel_state, channel_hv_set),
                    ).bind_enabled_from(channel_hv_enable, "value")

                    # Voltage
                    ui.label().bind_text_from(
                        channel_state,
                        "hv",
                        backward=lambda hv: f"{hv:.1f} V",
                    ).classes("text-right")

                    # Current
                    ui.label().bind_text_from(
                        channel_state,
                        "current",
                        backward=lambda i: f"{1000 * i:.1f} mA",
                    ).classes("text-right")

                    if channel == 0:
                        # Voltage history (spans 3 rows)
                        timeseries = TimeSeriesPlot(
                            yaxis_title="Voltage / V",
                        )
                        timeseries.plot.classes("row-span-3 w-full h-40 self-center")
                        self.hv_timeseries.append(
                            (
                                timeseries,
                                get_hv_timeseries_updater(slot_state),
                            )
                        )
                        # Current history (spans 3 rows)
                        _timeseries = TimeSeriesPlot(
                            yaxis_title="Current / mA",
                        )
                        _timeseries.plot.classes("row-span-3 w-full h-40 self-center")
                        self.current_timeseries.append(
                            (
                                _timeseries,
                                get_current_timeseries_updater(slot_state),
                            )
                        )


    async def update_state(self):
        """Attempts to update the Phantom HV state buffer. On first success,
        builds the UI. On failure, displays a notification and 'connecting'
        message."""

        if self.update_timer:
            self.update_timer.remove(self.update_timer)
            self.update_timer = None

        try:
            await run.io_bound(self.hv_state.update)
        except (iostack.TimeoutError, OSError):
            self.num_failures += 1
            reconnect_interval = self.default_update_interval * 2 ** min(
                6, self.num_failures
            )
            if (
                self.timeout_notification is None
                or self.timeout_notification.visible == False
            ):
                ui.notify(
                    "Lost connection to Phantom HV - will periodically attempt to reconnect..."
                )
            if self.timeout_notification is None:
                with ui.page_sticky("top-right", 8, 8) as self.timeout_notification:
                    with ui.row().classes("items-center bg-purple-900 p-2 rounded"):
                        ui.spinner(color="text-current")
                        ui.label("Connecting...")
            else:
                self.timeout_notification.set_visibility(True)

            self.update_timer = ui.timer(
                reconnect_interval,
                self.update_state,
                once=True,
            )
            return

        now = time.time()
        if self.log_time <= now:
            for slot in range(self.num_slots):
                slot_state = self.hv_state.slot[slot]
                print(f"phantomhv,address={self.host},slot={slot} hv_unlocked={slot_state.hv_unlocked},hv_unlocked_ext={slot_state.hv_unlocked_ext} {1e9 * slot_state.last_update:.0f}", flush=False)
                for channel in range(3):
                    channel_state = slot_state.channel[channel]
                    print(f"phantomhv,address={self.host},slot={slot},channel={channel} hv_enabled={channel_state.hv_enabled},hv_set_volt={channel_state.hv_set},hv_volt={channel_state.hv},current_ampere={channel_state.current} {1e9 * channel_state.last_update:.0f}", flush=False)

            self.log_time += self.log_interval
            while self.log_time < now:
                self.log_time += self.log_interval

            print(end="", flush=True)

        self.num_failures = 0
        if self.timeout_notification is not None:
            self.timeout_notification.set_visibility(False)

        if self.update_time is None:
            self.build_ui()  # it's the first time we've succeeded in connecting: build the UI
            self.update_time = now + self.default_update_interval
        else:
            self.update_time += self.default_update_interval
            while self.update_time < now:
                self.update_time += self.default_update_interval

        for timeseries, update in self.hv_timeseries + self.current_timeseries:
            x, y = update()
            timeseries.update(x, y)

        self.update_timer = ui.timer(
            self.update_time - now,
            self.update_state,
            once=True,
        )


def to_plotly_json_with_config(self):
    json = self.to_dict()
    json["config"] = {"staticPlot": True}
    return json


class TimeSeriesPlot:
    """Plotly-based time series plot for NiceGUI."""

    def __init__(
        self,
        xaxis_title=None,
        yaxis_title=None,
        xaxis_tickangle=0,
    ):
        self.fig = go.Figure()
        self.fig.update_layout(
            template="plotly_dark",
            font_family="'Source Code Pro', 'Source Code Variable', Courier, monospace",
            uirevision=True,
            datarevision=True,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(
                title=xaxis_title,
                tickangle=xaxis_tickangle,
                automargin="bottom",
            ),
            yaxis=dict(title=yaxis_title, tickformat="~r"),
        )
        self.plot = ui.plotly(self.fig)
        self.fig.to_plotly_json = types.MethodType(to_plotly_json_with_config, self.fig)

    def update(self, x, y):
        if self.fig.data:
            for i, _y in enumerate(y.T):
                self.fig.data[i]["x"] = x
                self.fig.data[i]["y"] = _y
        else:
            for i, _y in enumerate(y.T):
                self.fig.add_trace(go.Scatter(x=x, y=_y, name=str(i), hoverinfo="none"))

        self.plot.update()
