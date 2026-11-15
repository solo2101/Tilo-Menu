#!/usr/bin/env python3
# GPL-3.0-or-later, from GnoMenu 2.9.1 launcher by Whise.
# Ported to Python 3. Panel-button stage only.

import os
import sys
from pathlib import Path

# Limit BLAS worker creation before Globals imports NumPy. On smaller
# Fedora VMs, excessive worker threads prevent Glycin from spawning.
# Override system-wide BLAS defaults; opt out with TILOMENU_BLAS_THREADS.
blas_threads = os.environ.get('TILOMENU_BLAS_THREADS', '1')
for variable in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[variable] = blas_threads

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib' / 'tilomenu'))
from TiloMenu import main


if __name__ == '__main__':
    sys.exit(main())
