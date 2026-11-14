#!/usr/bin/env python3
# GPL-3.0-or-later, from GnoMenu 2.9.1 launcher by Whise.
# Ported to Python 3. Panel-button stage only.

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib' / 'tilomenu'))
from TiloMenu import main


if __name__ == '__main__':
    sys.exit(main())
