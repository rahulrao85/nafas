"""Nafas — a CPAP-adherence behaviour loop.

Detect a lapse or a mask leak, name the likely barrier, offer one small action,
learn which actions work for this person, and keep progress through setbacks.
"""

import sys

__version__ = "0.1.0"

# Gadgetbridge uploads are read in memory with sqlite3's Connection.deserialize, which Python 3.10 lacks.
# Fail here with one clear line rather than deep inside an upload or test run.
if sys.version_info < (3, 11):
    raise RuntimeError(f"Nafas needs Python 3.11 or later; this is Python {sys.version.split()[0]}. "
                       "See 'Run it' in README.md.")
