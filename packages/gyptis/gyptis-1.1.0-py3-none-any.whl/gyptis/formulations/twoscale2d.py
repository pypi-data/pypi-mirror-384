#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.1.0
# License: MIT
# See the documentation at gyptis.gitlab.io


from .formulation import *


class TwoScale2D(Formulation):
    def __init__(
        self,
        geometry,
        coefficients,
        function_space,
        boundary_conditions=None,
        degree=1,
        direction="x",
        case="epsilon",
    ):
        if boundary_conditions is None:
            boundary_conditions = {}
        super().__init__(
            geometry,
            coefficients,
            function_space,
            boundary_conditions=boundary_conditions,
            degree=degree,
        )
        self.epsilon, self.mu = self.coefficients
        self.direction = direction
        self.case = case

        if self.case == "mu":
            self.xi = self.mu.to_xi()
            self.chi = self.epsilon.to_chi()
        else:
            self.xi = self.epsilon.to_xi()
            self.chi = self.mu.to_chi()
        self.pec_boundaries = prepare_boundary_conditions(boundary_conditions)

    def poisson(self, u, v, xi, domain="everywhere"):
        if domain == []:
            return 0
        e = Constant((1, 0)) if self.direction == "x" else Constant((0, 1))
        form = [inner(xi * grad(u), grad(v))]
        form.append(dot(xi * e, grad(v)))
        return (form[0] + form[1]) * self.dx(domain)

    def _weak(self, u, v):
        xi = self.xi.as_subdomain()
        xi_dict = self.xi.as_property()
        dom_func, dom_no_func = find_domains_function((self.xi, self.chi))
        form = self.poisson(u, v, xi, domain=dom_no_func)
        for dom in dom_func:
            form += self.poisson(u, v, xi_dict[dom], domain=dom)
        return form.real + form.imag

    @property
    def weak(self):
        u = self.trial
        v = self.test
        return self._weak(u, v)

    def build_pec_boundary_conditions(self, applied_function):
        if self.case == "epsilon" and self.pec_boundaries != []:
            # FIXME: project is slow, avoid it.
            applied_function = project_iterative(
                applied_function, self.real_function_space
            )
            return build_pec_boundary_conditions(
                self.pec_boundaries,
                self.geometry,
                self.function_space,
                applied_function,
            )
        else:
            return []

    def build_boundary_conditions(self):
        applied_function = Constant(0)
        self._boundary_conditions = self.build_pec_boundary_conditions(applied_function)
        return self._boundary_conditions
