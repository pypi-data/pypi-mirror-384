import functools
import xarray as xr
from numpy import array, arange
from importlib_resources import files


@functools.cache
def read_coeffs(file):
    return xr.open_dataset(files('pyspammodel._coeffs').joinpath(file))


def get_aero_spam_coeffs():
    return (read_coeffs('_aero_spam_bands_coeffs.nc').copy(), read_coeffs('_aero_spam_lines_coeffs.nc').copy(),
            read_coeffs('_aero_spam_full_coeffs.nc').copy())


def get_solar_spam_coeffs():
    return read_coeffs('_solar_spam_coeffs.nc').copy()


def calc_diff_photon_flux(energy_flux):
    h = 6.62607015e-34
    c = 299792458
    l = array(arange(0.5, 190.5, 1)) * 1e-9
    return array([f / (h * c / l) for f, l in zip(energy_flux, l)])


def calc_diff_energy_flux(photon_flux):
    h = 6.62607015e-34
    c = 299792458
    l = array(arange(0.5, 190.5, 1)) * 1e-9
    return array([p * (h * c / l) for p, l in zip(photon_flux, l)])
