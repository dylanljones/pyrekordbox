# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2022-04-10

"""Package logger configuration."""

import logging

logger = logging.getLogger("pyrekordbox")

# Logging format
frmt = "[%(asctime)s] %(name)s:%(levelname)-8s - %(message)s"
formatter = logging.Formatter(frmt, datefmt="%H:%M:%S")

# Set up console logger
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
logger.addHandler(sh)

# Set logging level
logger.setLevel(logging.WARNING)
