#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess

def run_with_mate_panel_control() -> bool:
    cmd = shutil.which("mate-panel-control")
    if not cmd:
        return False
    try:
        subprocess.run([cmd, "--run-dialog"], check=True)
        return True
    except Exception:
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
        atom_run = disp.intern_atom("_MATE_PANEL_ACTION_RUN_DIALOG")
        data = (32, [atom_run, X.CurrentTime, 0, 0, 0])
        ev = protocol.event.ClientMessage(window=root, client_type=atom_action, data=data)
        # send to root with common masks
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
    print("Run dialog not triggered", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
