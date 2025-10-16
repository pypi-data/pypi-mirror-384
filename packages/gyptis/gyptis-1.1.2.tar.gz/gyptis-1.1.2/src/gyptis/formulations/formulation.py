#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.1.2
# License: MIT
# See the documentation at gyptis.gitlab.io

"""
Finite element weak formulations.
"""

from abc import ABC, abstractmethod

import numpy as np
from scipy.constants import epsilon_0, mu_0

from .. import dolfin
from ..bc import *
from ..complex import *
from ..sources import *
from ..utils.helpers import project_iterative


class Formulation(ABC):
    def __init__(
        self,
        geometry,
        coefficients,
        function_space,
        source=None,
        boundary_conditions=None,
        modal=False,
        degree=1,
        dim=None,
    ):
        if boundary_conditions is None:
            boundary_conditions = {}
        self.geometry = geometry
        self.coefficients = coefficients
        self.function_space = function_space
        if source is not None:
            source.domain = geometry.mesh
        self.source = source
        self.trial = TrialFunction(self.function_space)
        self.test = TestFunction(self.function_space)
        self.boundary_conditions = boundary_conditions
        self.modal = modal
        self.degree = degree
        _dim = self.trial.real.ufl_shape
        _dim = 1 if _dim == () else _dim[0]
        self.dim = dim or _dim
        self.measure = geometry.measure
        self.dx = self.measure["dx"]
        self.ds = self.measure["ds"]
        self.dS = self.measure["dS"]

        self.element = self.function_space.split()[0].ufl_element()
        self.real_function_space = dolfin.FunctionSpace(
            self.geometry.mesh, self.element
        )

    def build_lhs(self):
        self.lhs = dolfin.lhs(self.weak)
        return self.lhs

    def build_rhs(self):
        self.rhs = dolfin.rhs(self.weak)
        if self.rhs.empty():
            if self.element.value_size() == 3:
                dummy_vect = as_vector(
                    [dolfin.DOLFIN_EPS, dolfin.DOLFIN_EPS, dolfin.DOLFIN_EPS]
                )
                dummy_form = dot(dummy_vect, self.trial) * self.dx
            else:
                dummy_form = dolfin.DOLFIN_EPS * self.trial * self.dx
            self.rhs = dummy_form.real + dummy_form.imag
        return self.rhs

    def _set_rhs(self, custom_rhs):
        self.rhs = custom_rhs
        return self.rhs

    @abstractmethod
    def weak(self):
        """Weak formulation"""
        pass

    @abstractmethod
    def build_boundary_conditions(self):
        pass


def is_dolfin_function(f):
    return (
        hasattr(f.real, "ufl_shape") or hasattr(f.imag, "ufl_shape")
        if iscomplex(f)
        else hasattr(f, "ufl_shape")
    )


def find_domains_function(coeffs, list_domains=None):
    dom_function = []
    for coeff in coeffs:
        list_domains = list_domains or list(coeff.dict.keys())

        dom_function += [k for k, v in coeff.dict.items() if is_dolfin_function(v)]
    dom_function = np.unique(dom_function).tolist()
    dom_no_function = [k for k in list_domains if k not in dom_function]
    return dom_function, dom_no_function
