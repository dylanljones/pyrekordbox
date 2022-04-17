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
# frmt = "[%(asctime)s] (%(process)d) - %(levelname)-7s - %(message)s"
formatter = logging.Formatter(frmt, datefmt="%H:%M:%S")

# Set up console logger
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
logger.addHandler(sh)

# # Set up file logger
# fh = logging.FileHandler("dqmc.log", mode="w")
# fh.setLevel(logging.DEBUG)
# fh.setFormatter(formatter)
# logger.addHandler(fh)

# Set logging level
logger.setLevel(logging.WARNING)
logging.root.setLevel(logging.NOTSET)
