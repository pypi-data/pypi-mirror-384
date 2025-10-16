#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.1.0
# License: MIT
# See the documentation at gyptis.gitlab.io


__all__ = [
    "Layered",
    "Lattice",
    "Scattering",
    "Grating",
    "PhotonicCrystal",
    "PlaneWave",
    "LineSource",
    "GaussianBeam",
    "Source",
    "Dipole",
    "BoxPML",
    "LayeredBoxPML",
    "Layered",
    "Geometry",
    "Homogenization2D",
    "Homogenization3D",
    "Waveguide",
]


from .geometry import *
from .models import *
from .models.metaclasses import _GratingBase, _ScatteringBase
from .sources import *


def _check_dimension(dim):
    if dim not in [2, 3]:
        raise ValueError("dimension must be 2 or 3")


class BoxPML(Geometry):
    """BoxPML(dim, box_size, box_center, pml_width, Rcalc=0, **kwargs)
    Computational domain with Perfectly Matched Layers (PMLs).

    Parameters
    ----------
    dim : int
        Geometric dimension (either 2 or 3, the default is 3).
    box_size : tuple of floats of length `dim`
        Size of the box: :math:`(l_x,l_y)` if `dim=2` or :math:`(l_x, l_y, l_z)` if `dim=3`.
    box_center : tuple of floats of length `dim`
        Size of the box: :math:`(c_x,c_y)` if `dim=2` or :math:`(c_x, c_y, c_z)` if `dim=3`.
    pml_width : tuple of floats of length `dim`
        Size of the PMLs: :math:`(h_x,h_y)` if `dim=2` or :math:`(h_x, h_y, h_z)` if `dim=3`.
    Rcalc : float
        Radius of the circle (in 2D) or sphere (in 3D) for the calculation of cross sections.
        The default is 0 so no geametrical entity will be created but the calculation
        of cross sections will fail.
    **kwargs : dictionary
        Additional parameters. See the parent class :class:`~gyptis.Geometry`.

    """

    def __new__(cls, dim=3, *args, **kwargs):
        if dim not in [2, 3]:
            raise ValueError("dimension must be 2 or 3")
        return BoxPML3D(*args, **kwargs) if dim == 3 else BoxPML2D(*args, **kwargs)


class Layered(Geometry):
    """Layered(dim, period, thicknesses, **kwargs)
    Layered media for diffraction problems, defining the periodic unit cell
    for mono or bi periodic gratings.

    Parameters
    ----------
    dim : int
        Geometric dimension (either 2 or 3, the default is 3).
    period : float or tuple
        In 2D, periodicity of the grating :math:`d` along :math:`x` (float).
        In 3D, periodicity of the grating :math:`(d_x,d_y)` along :math:`x`
        and :math:`y` (tuple of floats of lenght 2).
    thicknesses : :class:`~collections.OrderedDict`
        Dictionary containing physical names and thicknesses from bottom to top.
        (``thicknesses["phyiscal_name"]=thickness_value``)
    **kwargs : dictionary
        Additional parameters. See the parent class :class:`~gyptis.Geometry`.


    Examples
    --------

    >>> from collections import OrderedDict
    >>> from gyptis import Layered
    >>> t = OrderedDict(pml_bot=1, slab=3, pml_top=1)
    >>> lays = Layered(dim=2, period=1.3, thicknesses=t)
    >>> lays.build()

    """

    def __new__(cls, dim=3, *args, **kwargs):
        _check_dimension(dim)
        return Layered3D(*args, **kwargs) if dim == 3 else Layered2D(*args, **kwargs)


class Lattice(Geometry):
    """Lattice(vectors, **kwargs)
    Unit cell for periodic problems.

    Parameters
    ----------
    dim : int
        Geometric dimension (either 2 or 3, the default is 3).
    vectors : tuple
        In 2D, a tuple of lengh 2 with the :math:`(x,y)` coordinates of 2 basis vectors.
        In 3D, a tuple of lengh 3 with the :math:`(x,y,z)` coordinates of 3 basis vectors.
    **kwargs : dictionary
        Additional parameters. See the parent class :class:`~gyptis.Geometry`.
    """

    def __new__(cls, dim=3, *args, **kwargs):
        _check_dimension(dim)
        return Lattice3D(*args, **kwargs) if dim == 3 else Lattice2D(*args, **kwargs)


class Scattering(_ScatteringBase, Simulation):
    """Scattering(geometry, epsilon, mu, source=None, boundary_conditions={}, polarization="TM", modal=False, degree=1, pml_stretch=1 - 1j)
    Scattering problem.

    Parameters
    ----------
    geometry : :class:`~gyptis.Geometry`
        The meshed geometry
    epsilon : dict
        Permittivity in various subdomains.
    mu : dict
        Permeability in various subdomains.
    source : :class:`~gyptis.Source`
        Excitation (the default is None).
    boundary_conditions : dict
        Boundary conditions {"boundary": "condition"} (the default is {}).
        Valid condition is only "PEC".
    polarization : str
        Polarization case (only makes sense for 2D problems, the default is "TM").
    modal : str
        Perform modal analysis (the default is False).
    degree : int
        Degree of finite elements interpolation (the default is 1).
    pml_stretch : complex
        Complex coordinate stretch for te PMLs (the default is 1 - 1j).

    """

    def __new__(cls, *args, **kwargs):
        geom = kwargs.get("geometry") or args[0]
        _check_dimension(geom.dim)
        return Scatt3D(*args, **kwargs) if geom.dim == 3 else Scatt2D(*args, **kwargs)


class Grating(_GratingBase, Simulation):
    """Grating(geometry, epsilon, mu, source, boundary_conditions={}, polarization="TM", degree=1, pml_stretch=1 - 1j, periodic_map_tol=1e-8, propagation_constant=0.0)
    Grating problem.

    Parameters
    ----------
    geometry : :class:`~gyptis.Geometry`
        The meshed geometry
    epsilon : dict
        Permittivity in various subdomains.
    mu : dict
        Permeability in various subdomains.
    source : :class:`~gyptis.Source`
        Excitation (the default is None).
    boundary_conditions : dict
        Boundary conditions {"boundary": "condition"} (the default is {}).
        Valid condition is only "PEC".
    polarization : str
        Polarization case (only makes sense for 2D problems, the default is "TM").
    modal : str
        Perform modal analysis (the default is False).
    degree : int
        Degree of finite elements interpolation (the default is 1).
    pml_stretch : complex
        Complex coordinate stretch for te PMLs (the default is 1 - 1j).
    periodic_map_tol : float
        Tolerance for mapping boundaries (the default is 1e-8).
    propagation_constant : float
        Propagation constant along the periodicity. Only
        makes sense for modal analysis (the default is 0.0).


    """

    def __new__(cls, *args, **kwargs):
        geom = kwargs.get("geometry") or args[0]
        _check_dimension(geom.dim)
        if geom.dim == 3:
            return Grating3D(*args, **kwargs)
        else:
            return Grating2D(*args, **kwargs)


class PhotonicCrystal:
    """PhotonicCrystal(geometry, epsilon, mu, propagation_vector, boundary_conditions={}, polarization="TM", degree=1, eps=dolfin.DOLFIN_EPS, map_tol=1e-10)

    Photonic crystal class.

    Parameters
    ----------
    geometry : :class:`~gyptis.Geometry`
        The meshed geometry
    epsilon : dict
        Permittivity in various subdomains.
    mu : dict
        Permeability in various subdomains.
    propagation_vector : tuple of float
        The propagation vector of the mode
    boundary_conditions : dict or list of dict
        Boundary conditions of the simulation
    polarization : str
        Polarization of the mode
    degree : int
        The degree of the function space
    eps : float
        The tolerance for the periodic boundary conditions values
    map_tol : float
        The tolerance for the periodic boundary conditions mesh

    Notes
    -----
    Only 2D problems are supported for now.
    """

    def __new__(cls, *args, **kwargs):
        geom = kwargs.get("geometry") or args[0]
        _check_dimension(geom.dim)
        if geom.dim == 3:
            raise NotImplementedError
        else:
            return PhotonicCrystal2D(*args, **kwargs)


class LayeredBoxPML(Geometry):
    """LayeredBoxPML(dim, width, thicknesses, pml_width, **kwargs)
    Layered computational domain with Perfectly Matched Layers (PMLs).

    Parameters
    ----------
    dim : int
        Geometric dimension (either 2 or 3, the default is 3).
    width : float
        Lateral size of the box.
    thicknesses : :class:`~collections.OrderedDict`
        Dictionary containing physical names and thicknesses from bottom to top.
        (``thicknesses["phyiscal_name"]=thickness_value``)
    pml_width : tuple of floats of length `dim`
        Size of the PMLs: :math:`(h_x,h_y)`.
    **kwargs : dictionary
        Additional parameters. See the parent class :class:`~gyptis.Geometry`.

    """

    def __new__(cls, dim=2, *args, **kwargs):
        if dim not in [2, 3]:
            raise ValueError("dimension must be 2 or 3")
        if dim == 3:
            raise NotImplementedError
        return LayeredBoxPML2D(*args, **kwargs)


class Waveguide:
    """Waveguide(geometry, epsilon, mu, wavenumber, boundary_conditions={}, degree=(1,1), pml_stretch=1 - 1j,)

    Waveguide class.

    Parameters
    ----------
    geometry : :class:`~gyptis.LayeredBoxPML2D`
        The meshed geometry
    epsilon : dict
        Permittivity in various subdomains.
    mu : dict
        Permeability in various subdomains.
    wavenumber : tuple of float
        The wavenumber
    boundary_conditions : dict or list of dict
        Boundary conditions of the simulation
    degree : (int,int)
        The degrees of the function space
    pml_stretch : complex
        Complex coordinate stretch for te PMLs (the default is 1 - 1j).

    Notes
    -----
    Only 2D problems are supported for now.
    """

    def __new__(cls, *args, **kwargs):
        geom = kwargs.get("geometry") or args[0]
        _check_dimension(geom.dim)
        if geom.dim == 3:
            raise NotImplementedError
        else:
            return Waveguide(*args, **kwargs)
