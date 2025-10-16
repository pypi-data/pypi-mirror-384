#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.1.1
# License: MIT
# See the documentation at gyptis.gitlab.io

from .geometry import *


class Lattice2D(Geometry):
    def __init__(
        self,
        vectors,
        **kwargs,
    ):
        super().__init__(
            dim=2,
            **kwargs,
        )
        self.vectors = vectors
        self.vertices = [
            (0, 0),
            (self.vectors[0][0], self.vectors[0][1]),
            (
                self.vectors[0][0] + self.vectors[1][0],
                self.vectors[0][1] + self.vectors[1][1],
            ),
            (self.vectors[1][0], self.vectors[1][1]),
        ]
        p = [self.add_point(*v, 0) for v in self.vertices]
        curves = [self.add_line(p[i + 1], p[i]) for i in range(3)]
        curves.append(self.add_line(p[3], p[0]))
        cl = self.add_curve_loop(curves)
        ps = self.add_plane_surface([cl])
        self.cell = ps
        # self.add_physical(self.cell, "cell")

    @property
    def translation(self):
        return (
            self._translation_matrix([*self.vectors[0], 0]),
            self._translation_matrix([*self.vectors[1], 0]),
        )

    def get_periodic_bnds(self):
        # define lines equations
        def _is_on_line(p, p1, p2):
            x, y = p
            x1, y1 = p1
            x2, y2 = p2
            if x1 == x2:
                return np.allclose(x, x1)
            else:
                return np.allclose(y - y1, (y2 - y1) / (x2 - x1) * (x - x1))

        verts = self.vertices.copy()
        verts.append(self.vertices[0])

        # get all boundaries
        bnds = self.get_entities(1)
        maps = []
        for i in range(4):
            wheres = []
            for b in bnds:
                qb = gmsh.model.getParametrizationBounds(1, b[-1])
                B = []
                for p in qb:
                    val = gmsh.model.getValue(1, b[-1], p)
                    p = val[:2]
                    belongs = _is_on_line(p, verts[i + 1], verts[i])
                    B.append(belongs)
                alls = np.all(B)
                if alls:
                    wheres.append(b)
            maps.append(wheres)
        s = {}
        s["-1"] = [m[-1] for m in maps[-1]]
        s["+1"] = [m[-1] for m in maps[1]]
        s["-2"] = [m[-1] for m in maps[0]]
        s["+2"] = [m[-1] for m in maps[2]]
        return s

    def build(self, *args, **kwargs):
        periodic_id = self.get_periodic_bnds()
        gmsh.model.mesh.setPeriodic(
            1, periodic_id["+1"], periodic_id["-1"], self.translation[0]
        )
        gmsh.model.mesh.setPeriodic(
            1, periodic_id["+2"], periodic_id["-2"], self.translation[1]
        )
        super().build(*args, **kwargs)
