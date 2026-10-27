"""API package initialization.

Adds the app directory to sys.path so the legacy absolute imports used by the
backend modules continue to work when the project is imported from the repo root.
"""

from __future__ import annotations

import os
import sys

_api_dir = os.path.dirname(__file__)
if _api_dir not in sys.path:
    sys.path.insert(0, _api_dir)
