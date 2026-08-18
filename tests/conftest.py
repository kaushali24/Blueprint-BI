"""conftest.py – Project-level pytest configuration.

Adds the ``backend/`` directory to ``sys.path`` so that ``app.*`` imports
resolve correctly both when running pytest and when the IDE language server
analyses test files.

``pytest.ini`` already sets ``pythonpath = backend``, which handles pytest
runs.  This file ensures the path insertion also happens at module-import
time so that IDE tools (Pylance, pyright) that evaluate ``conftest.py``
eagerly can locate the ``app`` package without requiring the venv Python
interpreter to be explicitly configured in the IDE workspace.
"""

import sys
from pathlib import Path

# Insert <repo-root>/backend at the front of sys.path so that
# `import app.*` works regardless of which Python interpreter the
# IDE language server happens to use.
_BACKEND = Path(__file__).parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))
