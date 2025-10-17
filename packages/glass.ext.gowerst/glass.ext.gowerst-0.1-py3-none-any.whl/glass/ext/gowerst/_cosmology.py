import os
from functools import cached_property

import h5py
import numpy as np
from scipy.interpolate import CubicSpline


# convert from Gyr-1 to km Mpc-1 s-1
H_UNITS = 977.79222168


def make_log_interp(loga, y):
    """Create log(a), log(val) interpolator like pkdgrav3."""
    interp = CubicSpline(loga, np.log(y), bc_type="natural", extrapolate=False)
    return lambda z: np.exp(interp(-np.log1p(z)))


def make_dist_interp(z, x):
    """Create interpolator for dimensionless comoving distance."""
    interp = CubicSpline(z[::-1], x[::-1], bc_type="natural", extrapolate=False)
    return interp.antiderivative()


class Cosmology:
    h: float
    scale_factor0: float
    Omega_tot0: float
    Omega_b0: float
    Omege_dm0: float
    Omega_m0: float
    Omega_de0: float
    Omega_gamma0: float
    Omega_nu0: float
    w_0: float
    w_a: float

    def __init__(self, path: str | os.PathLike[str]) -> None:
        with h5py.File(path) as f:
            # this is where the input parameters are stored
            bg = f["background"]

            # get background parameters
            h = bg.attrs["h"]
            Omega_tot = bg.attrs["Omega_tot"]
            Omega_b = bg.attrs["Omega_b"]
            Omega_cdm = bg.attrs["Omega_cdm"]
            Omega_cdm_b = bg.attrs["Omega_cdm+b"]
            Omega_fld = bg.attrs["Omega_fld"]
            Omega_g = bg.attrs["Omega_g"]
            w_0 = bg.attrs["w_0"]
            w_a = bg.attrs["w_a"]

            # collect the neutrino parameters
            Omega_ncdm = []
            while (key := f"Omega_ncdm[{len(Omega_ncdm)}]") in bg.attrs:
                Omega_ncdm.append(bg.attrs[key])

            # get cosmological functions
            z = bg["z"][...]
            a = bg["a"][...]
            H = bg["H"][...]
            t = bg["t"][...]
            rho_crit = bg["rho_crit"][...]
            rho_tot = bg["rho_tot"][...]
            rho_b = bg["rho_b"][...]
            rho_cdm = bg["rho_cdm"][...]
            rho_cdm_b = bg["rho_cdm+b"][...]
            rho_fld = bg["rho_fld"][...]
            rho_g = bg["rho_g"][...]

            # collect the neutrino functions
            rho_ncdm = []
            for i in range(len(Omega_ncdm)):
                rho_ncdm.append(bg[f"rho_ncdm[{i}]"][...])

            # get units used in file
            unit_length = f["units"].attrs["unit length"]
            unit_mass = f["units"].attrs["unit mass"]
            unit_time = f["units"].attrs["unit time"]

            # done with reading file

        # check units
        if unit_length != "Mpc" or unit_mass != "10**(10)*m_sun" or unit_time != "Gyr":
            raise ValueError(
                f"{path}: file uses incompatible units: {unit_length}, {unit_mass}, {unit_time}"
            )

        # scale to standard units
        H = H * H_UNITS

        # determine scale factor
        a0 = np.mean(a * (1 + z))
        if not np.allclose(a, a0 / (1 + z), atol=1e-15, rtol=1e-15):
            raise ValueError("inconsistent scale factor")

        # cosmological parameters
        self.h = h
        self.scale_factor0 = a0
        self.Omega_tot0 = Omega_tot
        self.Omega_b0 = Omega_b
        self.Omega_dm0 = Omega_cdm
        self.Omega_m0 = Omega_cdm_b
        self.Omega_de0 = Omega_fld
        self.Omega_gamma0 = Omega_g
        self.Omega_nu0 = sum(Omega_ncdm)
        self.w_0 = w_0
        self.w_a = w_a

        # cosmological function interpolation
        # this matches what is done by pkdgrav3 internally
        x = np.log(a / a0)
        self._H = make_log_interp(x, H)
        self._age = make_log_interp(x, t)
        self._critical_density = make_log_interp(x, rho_crit * 1e10)
        self._Omega_tot = make_log_interp(x, rho_tot / rho_crit)
        self._Omega_b = make_log_interp(x, rho_b / rho_crit)
        self._Omega_dm = make_log_interp(x, rho_cdm / rho_crit)
        self._Omega_m = make_log_interp(x, rho_cdm_b / rho_crit)
        self._Omega_de = make_log_interp(x, rho_fld / rho_crit)
        self._Omega_gamma = make_log_interp(x, rho_g / rho_crit)
        self._Omega_nu = make_log_interp(x, sum(rho_ncdm) / rho_crit)

        # curvature parameter for convenience
        if np.abs(1 - Omega_tot) < 1e-15:
            self._K = 0.0
        elif Omega_tot < 1:
            self._K = np.sqrt(1 - Omega_tot)
        else:
            self._K = -np.sqrt(Omega_tot - 1)

        # interpolation for distance functions
        self._dist = make_dist_interp(z, 100 * h / H)

    def __repr__(self) -> str:
        clsname = self.__class__.__name__
        attrs = [f"{k}={v!r}," for k, v in vars(self).items() if not k.startswith("_")]
        return f"{clsname}(\n    " + "\n    ".join(attrs) + "\n)"

    def H(self, z: float) -> float:
        return self._H(z)

    @cached_property
    def H0(self) -> float:
        return self.h * 100.0

    def H_over_H0(self, z: float) -> float:
        return self.H(z) / self.H0

    def scale_factor(self, z: float) -> float:
        return self.scale_factor0 / (1 + z)

    def comoving_distance(self, z: float, z2: float | None = None) -> float:
        x = self._dist(z) if z2 is None else self._dist(z2) - self._dist(z)
        return self.hubble_distance * x

    def transverse_comoving_distance(self, z: float, z2: float | None = None) -> float:
        x = self._dist(z) if z2 is None else self._dist(z2) - self._dist(z)
        k = self._K
        if k > 0:
            x = np.sinh(x * k) / k
        elif k < 0:
            x = np.sin(x * k) / k
        return self.hubble_distance * x

    @cached_property
    def hubble_distance(self) -> float:
        return 299792.458 / self.H0

    def age(self, z: float) -> float:
        return self._age(z)

    def critical_density(self, z: float) -> float:
        return self._critical_density(z)

    @cached_property
    def critical_density0(self) -> float:
        return self._critical_density(0.0)

    def Omega_tot(self, z: float) -> float:
        return self._Omega_tot(z)

    def Omega_b(self, z: float) -> float:
        return self._Omega_b(z)

    def Omega_dm(self, z: float) -> float:
        return self._Omega_dm(z)

    def Omega_m(self, z: float) -> float:
        return self._Omega_m(z)

    def Omega_de(self, z: float) -> float:
        return self._Omega_de(z)

    def Omega_gamma(self, z: float) -> float:
        return self._Omega_gamma(z)

    def Omega_nu(self, z: float) -> float:
        return self._Omega_nu(z)

    @cached_property
    def Omega_k0(self) -> float:
        return 1 - self.Omega_tot0

    def Omega_k(self, z: float) -> float:
        return 1 - self.Omega_tot(z)
