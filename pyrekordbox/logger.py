# coding: utf-8
#
# This code is part of pyrekordbox.
#
# Copyright (c) 2022, Dylan Jones

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
logging.root.setLevel(logging.NOTSET)
