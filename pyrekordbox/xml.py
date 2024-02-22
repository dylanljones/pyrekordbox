# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2022-04-10

from .rbxml import *  # noqa: F401, F403
from .utils import warn_deprecated as _warn_deprecated

_warn_deprecated("pyrekordbox.xml", "pyrekordbox.rbxml", remove_in="0.4.0")
