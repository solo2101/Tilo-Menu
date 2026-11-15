"""Launch original TiloMenu-Settings.py as a real GTK3 child process.

Opening the notebook inside an existing Python process does not verify
that the MATE applet's external Preferences command will start.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

settings = Path(__file__).resolve().parents[1] / "src/lib/tilomenu/TiloMenu-Settings.py"
process = subprocess.Popen(
    [sys.executable, str(settings)],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    env=os.environ.copy())
try:
    time.sleep(1.5)
    if process.poll() is not None:
        out, err = process.communicate(timeout=3)
        raise AssertionError(
            "Original external Preferences process exited on startup: "
            + (out + err).decode("utf-8", errors="replace"))
    print("PASS: original Preferences process stays open under GTK3")
finally:
    if process.poll() is None:
        process.terminate()
        try:
            process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
