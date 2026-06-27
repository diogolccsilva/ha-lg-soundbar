"""Test path setup.

The protocol module only depends on pycryptodome, so we import it directly from
the integration folder. This avoids importing the package ``__init__`` (which
pulls in Home Assistant) and lets the wire protocol be tested in isolation.
"""

import pathlib
import sys

_PROTOCOL_DIR = (
    pathlib.Path(__file__).resolve().parent.parent
    / "custom_components"
    / "lg_soundbar_plus"
)
sys.path.insert(0, str(_PROTOCOL_DIR))
