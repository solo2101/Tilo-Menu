#!/usr/bin/env python3

# Standalone launcher

import sys
import os

try:
    with open("/etc/tilo/prefix", "r") as f:
        INSTALL_PREFIX = f.read().strip() or "/usr"
except Exception:
    INSTALL_PREFIX = "/usr"

exe = sys.executable

if len(sys.argv) == 2:
    arg = sys.argv[1]
    if arg == "run-in-tray":
        os.system(f'{exe} -u {INSTALL_PREFIX}/lib/tilo/TiloTray.py')
    elif arg == "unity":
        os.system(f'{exe} -u {INSTALL_PREFIX}/lib/tilo/TiloUnity.py')
    elif arg == "settings":
        os.system(f'{exe} -u {INSTALL_PREFIX}/lib/tilo/Tilo-Settings.py')
    else:
        os.system(f'{exe} -u {INSTALL_PREFIX}/lib/tilo/Tilo.py {arg}')

if len(sys.argv) != 2 or sys.argv[1] == "--help":
    print("\nUsage: Tilo.py [Command] \n")
    print("Command:\tWhat it does:\n")
    print("run-in-window\truns independant of mate-panel")
    print("run-in-tray\truns in system tray")
    print("settings\topens settings window")
    print("debug\t\truns in debug mode in mate-panel")
    print("--help\t\tdisplay this help text")
