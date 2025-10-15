#!/usr/bin/env python3
# Tilo session manager (MATE only)

import sys
import os
import argparse

try:
    import dbus
except Exception:
    dbus = None


def mate_session(action: str) -> bool:
    if dbus is None:
        return False
    try:
        bus = dbus.SessionBus()
        obj = bus.get_object("org.mate.SessionManager", "/org/mate/SessionManager")
        sm = dbus.Interface(obj, "org.mate.SessionManager")
    except Exception:
        return False

    try:
        if action == "logout":
            sm.Logout(0)
            return True
        if action == "reboot":
            try:
                sm.RequestReboot()
            except Exception:
                sm.Shutdown()
            return True
        if action == "shutdown":
            try:
                sm.RequestShutdown()
            except Exception:
                sm.Shutdown()
            return True
    except Exception:
        return False
    return False


def mate_legacy_power(action: str) -> bool:
    # Older MATE provided org.mate.PowerManagement on the session bus
    if dbus is None:
        return False
    if action not in ("suspend", "hibernate", "reboot", "shutdown"):
        return False
    try:
        bus = dbus.SessionBus()
        obj = bus.get_object("org.mate.PowerManagement", "org/mate/PowerManagement")
        pm = dbus.Interface(obj, "org/mate.PowerManagement")
        if action == "suspend":
            pm.Suspend()
        elif action == "hibernate":
            pm.Hibernate()
        elif action == "reboot":
            pm.Reboot()
        elif action == "shutdown":
            pm.Shutdown()
        return True
    except Exception:
        return False


def upower(action: str) -> bool:
    # MATE uses UPower for suspend and hibernate on modern systems
    if dbus is None:
        return False
    if action not in ("suspend", "hibernate"):
        return False
    try:
        bus = dbus.SystemBus()
        obj = bus.get_object("org.freedesktop.UPower", "/org/freedesktop/UPower")
        up = dbus.Interface(obj, "org.freedesktop.UPower")
        if action == "suspend":
            up.Suspend()
        else:
            up.Hibernate()
        return True
    except Exception:
        return False


def systemctl(action: str) -> bool:
    # Last resort, still desktop agnostic but not another DE
    mapping = {
        "shutdown": "systemctl poweroff",
        "reboot": "systemctl reboot",
        "suspend": "systemctl suspend",
        "hibernate": "systemctl hibernate",
        "logout": f"loginctl terminate-user {os.getuid()}",
    }
    cmd = mapping.get(action)
    if not cmd:
        return False
    return os.system(cmd) == 0


def main():
    p = argparse.ArgumentParser(description="Tilo session manager for MATE")
    p.add_argument("action", choices=["shutdown", "reboot", "suspend", "hibernate", "logout"])
    args = p.parse_args()
    action = args.action

    # MATE SessionManager handles logout, reboot, shutdown
    if action in ("logout", "reboot", "shutdown"):
        if mate_session(action):
            print(f"{action} requested via org.mate.SessionManager")
            return
        # legacy MATE fallback for reboot/shutdown
        if mate_legacy_power(action):
            print(f"{action} requested via org.mate.PowerManagement")
            return
        if systemctl(action):
            print(f"{action} executed via systemctl")
            return
        print(f"Failed to {action}")
        sys.exit(1)

    # suspend and hibernate
    if mate_legacy_power(action):
        print(f"{action} requested via org.mate.PowerManagement")
        return
    if upower(action):
        print(f"{action} requested via UPower")
        return
    if systemctl(action):
        print(f"{action} executed via systemctl")
        return

    print(f"Failed to {action}")
    sys.exit(1)


if __name__ == "__main__":
    main()
