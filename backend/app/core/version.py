"""Reads the git commit the running container was built from.

Set via the ``GIT_COMMIT`` build arg (see ``backend/Dockerfile`` and
``docker-compose.yml``) baked in as the ``PARCEL_SERVER_COMMIT`` environment
variable - there is no ``.git`` directory inside the image to inspect at
runtime, and no in-repo release process to compare against otherwise.
"""

from __future__ import annotations

import os

COMMIT_ENV_VAR = "PARCEL_SERVER_COMMIT"


def get_running_commit() -> str | None:
    """Returns the full commit SHA the running image was built from, or
    ``None`` if it wasn't set at build time (e.g. local/dev runs)."""
    commit = os.environ.get(COMMIT_ENV_VAR)
    return commit if commit and commit != "unknown" else None
