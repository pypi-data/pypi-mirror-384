#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.1.0
# License: MIT
# See the documentation at gyptis.gitlab.io


__all__ = [
    "parloop",
    "mpi_print",
]


import sys
from functools import wraps

from joblib import Parallel, delayed

from .. import dolfin


def parloop(n_jobs=1, prefer=None):
    def deco_parloop(func):
        """
        Decorate a function to parallelize.
        """

        @wraps(func)
        def my_func(*args, **kwargs):
            other_args = args[1:]
            return Parallel(n_jobs=n_jobs, prefer=prefer)(
                delayed(func)(x, *other_args, **kwargs) for x in args[0]
            )

        return my_func

    return deco_parloop


def mpi_print(*args, **kwargs):
    if dolfin.MPI.rank(dolfin.MPI.comm_world) == 0:
        print(*args, **kwargs)
        sys.stdout.flush()
