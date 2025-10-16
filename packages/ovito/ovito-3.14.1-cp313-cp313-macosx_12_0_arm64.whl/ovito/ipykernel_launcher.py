"""
This script is executed on application startup if OVITO Pro is launched as
an IPython kernel (as specified in the kernel.json file).

The script is responsible for starting the IPython kernel and setting it up for Qt event loop processing.
"""

import sys
from pathlib import Path

if __name__ == "__main__":
    # Remove the CWD from sys.path while we load stuff.
    # This is added back by InteractiveShellApp.init_path()
    if sys.path[0] == "" or Path(sys.path[0]) == Path.cwd():
        del sys.path[0]

    from ipykernel.kernelapp import IPKernelApp
    from ipykernel.eventloops import enable_gui

    app = IPKernelApp.instance()
    app.initialize()
    enable_gui("qt", app.kernel)
    app.start()