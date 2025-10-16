#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.1.0
# License: MIT
# See the documentation at gyptis.gitlab.io

__all__ = ["logger", "set_log_level"]


import logging
import sys

from loguru import logger

from .. import dolfin


def set_log_level(level, level_dolfin=None):
    global logger
    logger.remove()
    logformat = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> -- <level>{message}</level>"
    logger.add(sys.stderr, format=logformat, level=level, colorize=True)
    if level_dolfin == None:
        level_dolfin = level
    dolfin.set_log_level(level_dolfin)


set_log_level(logging.INFO, logging.ERROR)
