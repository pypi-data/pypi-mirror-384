# --- Deprecation notice (shown once per process) ---
import os as _os
import warnings as _warnings

if not _os.environ.get("OPENFHE_SILENCE_DEPRECATION"):
    _flag = "_OPENFHE_DEPRECATION_SHOWN"
    if not globals().get(_flag):
        globals()[_flag] = True
        _warnings.warn("⚠️  Deprecation notice: This is the last OpenFHE wheel built for Ubuntu 20.04. "
                       "No new OpenFHE builds will be published for this OS.",
                       category=UserWarning,
                       stacklevel=2,
        )

from .openfhe import *
