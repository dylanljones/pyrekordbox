# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2023-08-07

from ..utils import warn_deprecated as _warn_deprecated
from .models import *  # noqa: F403

_warn_deprecated(
    "pyrekordbox.masterdb.tables",
    "pyrekordbox.masterdb.models",
    hint="The tables module was renamed to models!",
    remove_in="0.6.0",
)
