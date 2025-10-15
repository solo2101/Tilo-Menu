#!/usr/bin/env python3

import sys
import shutil
import subprocess

def run_with_mate_panel_control() -> bool:
    cmd = shutil.which("mate-panel-control")
    if not cmd:
        return False
    for arg in ("--main-menu", "--show-menu"):
        try:
            subprocess.run([cmd, arg], check=True)
            return True
        except Exception:
            continue
    return False

def run_with_xlib() -> bool:
    try:
        from Xlib.display import Display
        from Xlib import X, protocol
    except Exception:
        return False
    try:
        disp = Display()
        root = disp.screen().root
        atom_action = disp.intern_atom("_MATE_PANEL_ACTION")
        atom_menu = disp.intern_atom("_MATE_PANEL_ACTION_MAIN_MENU")
        data = (32, [atom_menu, X.CurrentTime, 0, 0, 0])
        ev = protocol.event.ClientMessage(window=root, client_type=atom_action, data=data)
        root.send_event(ev, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
        disp.flush()
        return True
    except Exception:
        return False

def main():
    if run_with_mate_panel_control():
        sys.exit(0)
    if run_with_xlib():
        sys.exit(0)
    print("mate menu not triggered", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
