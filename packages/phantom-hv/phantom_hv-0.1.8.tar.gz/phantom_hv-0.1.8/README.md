# Phantom HV Control & Monitoring Software

This repository contains software to control and monitor a Phantom HV crate via
Ethernet. The Phantom HV hardware is a modular 3-RU system that combines
high-voltage supplies and high-frequency pulse pick-off circuits to operate
photomultiplier tubes (PMTs). It has been designed for the
[SWGO](https://www.swgo.org/) and lab applications.

<img alt="Phantom HV crate equipped with one master and one slave module."
     src="https://github.com/fwerner/phantom-hv/blob/main/phantom-hv-crate.jpg?raw=true"
     height="250px">

## Software installation

You can find the newest packaged release of this library on
[PyPi](https://pypi.org/project/phantom-hv/). Untagged versions
are released on [TestPyPi](https://test.pypi.org/project/phantom-hv/) as well.

Install via `pip install phantom-hv`.

Upgrade to the newest release with `pip install -U phantom-hv`.

## Requirements

- Python 3 for the core library and command-line interface
- nicegui, pywebview, plotly and numpy for the Web UI (install via conda/mamba
  or pip)
  - note that pywebview (which is only needed for displaying the UI in a native
    application window) may require additional GUI framework components with
    Python extensions, especially on an otherwise headless server (e.g. by
    installing `pywebview[qt]`, see the
    [documentation](https://pywebview.flowrl.com/guide/installation.html))

## Tools

If installed via pip this library provides two tools:

- `phantomhv-ctl` is a command-line interface to control and monitor a Phantom
  HV module
- `phantomhv-webui` provides a web interface with realtime plotting

### `phantomhv-ctl` command-line tool

```
usage: phantomhv-ctl [-h] {boot,reset,flash,unlock-hv,lock-hv,enable-hv,disable-hv,set,monitor} ...

Low-level control and monitoring command-line tool for Phantom HV modules.

positional arguments:
  {boot,reset,flash,unlock-hv,lock-hv,enable-hv,disable-hv,set,monitor}
    boot                boot application slot
    reset               reset into bootloader
    flash               flash binary firmware image into application slot
    unlock-hv           enable HV
    lock-hv             disable HV
    enable-hv           enable HV channel
    disable-hv          disable HV channel
    set                 set hardware registers
    monitor             continuously read and print slave states

options:
  -h, --help            show this help message and exit
```

### `phantomhv-webui` web interface

<img alt="Screen recording of the Phantom HV Web UI being run in native mode."
     src="https://github.com/fwerner/phantom-hv/blob/main/webui-recording.gif?raw=true">

```
usage: phantomhv-webui [-h] [--address ip:port] [--num-slots {1,2,3,4,5,6,7,8}] [--show | --bind hostname:port]

Web UI to monitor and control a Phantom HV crate.

options:
  -h, --help            show this help message and exit
  --address ip:port     IP address or hostname of the device (default: 192.168.1.115:512)
  --num-slots {1,2,3,4,5,6,7,8}
                        number of modules to display (default: 1)
  --show                open UI in native window
  --bind hostname:port  bind web server to a specific network interface/port (default: 127.0.0.1:8080; use 0.0.0.0 to bind to all interfaces)
```
