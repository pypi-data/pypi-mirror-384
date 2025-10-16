#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.1.0
# License: MIT
# See the documentation at gyptis.gitlab.io


import distutils.core
import os
import platform
import sys
import time

import dolfin
import pkg_resources
import psutil
from IPython.core.magic import Magics, line_magic, magics_class
from IPython.display import HTML, display

import gyptis

dir_path = os.path.dirname(os.path.realpath(__file__))


def local_hardware_info():
    """Basic hardware information about the local machine.
    Gives actual number of CPU's in the machine, even when hyperthreading is
    turned on. CPU count defaults to 1 when true count can't be determined.
    Returns:
        dict: The hardware information.
    """
    return {
        "python_compiler": platform.python_compiler(),
        "python_build": ", ".join(platform.python_build()),
        "python_version": platform.python_version(),
        "os": platform.system(),
        "memory": psutil.virtual_memory().total / (1024**3),
        "cpus": psutil.cpu_count(logical=False) or 1,
    }


@magics_class
class VersionTable(Magics):
    """A class of status magic functions."""

    @line_magic
    def gyptis_version_table(self, line="", cell=None):
        """
        Print an HTML-formatted table with version numbers for Gyptis and its
        dependencies. This should make it possible to reproduce the environment
        and the calculation later on.
        """

        html = "<h3>Version Information</h3>" + "<table>"
        html += "<tr><th>Package</th></tr>"

        p = ["numpy", "scipy", "matplotlib"]
        packages = [
            ("<code>gyptis</code>", gyptis.__version__),
            ("<code>dolfin</code>", dolfin.__version__),
        ]
        for pkg in p:
            ver = pkg_resources.get_distribution(pkg).version

            packages.append((f"<code>{pkg}</code>", ver))

        for name, version in packages:
            html += f"<tr><td>{name}</td><td>{version}</td></tr>"

        html += "<tr><th>System information</th></tr>"

        local_hw_info = local_hardware_info()
        sys_info = [
            ("Python version", local_hw_info["python_version"]),
            ("Python compiler", local_hw_info["python_compiler"]),
            ("Python build", local_hw_info["python_build"]),
            ("OS", f'{local_hw_info["os"]}'),
            ("CPUs", f'{local_hw_info["cpus"]}'),
            ("Memory (Gb)", f'{local_hw_info["memory"]}'),
        ]

        for name, version in sys_info:
            html += f"<tr><td>{name}</td><td>{version}</td></tr>"

        html += f"""<tr><td colspan='2'>{time.strftime("%a %b %d %H:%M:%S %Y %Z")}</td></tr>"""
        html += "</table>"

        return display(HTML(html))
