import numpy as np
import xarray as xr
import pyspammodel._misc as _m


class AeroSpam:
    '''
    Aero-SPAM model class.
    '''
    def __init__(self):
        self._bands_dataset, self._lines_dataset, self._full_dataset = _m.get_aero_spam_coeffs()

        self._full_coeffs = np.vstack((np.array(self._full_dataset['P1'], dtype=np.float64),
                                        np.array(self._full_dataset['P2'], dtype=np.float64),
                                        np.array(self._full_dataset['P3'], dtype=np.float64))).transpose()

        self._bands_coeffs = np.vstack((np.array(self._bands_dataset['P1'], dtype=np.float64),
                                        np.array(self._bands_dataset['P2'], dtype=np.float64),
                                        np.array(self._bands_dataset['P3'], dtype=np.float64))).transpose()

        self._lines_coeffs = np.vstack((np.array(self._lines_dataset['P1'], dtype=np.float64),
                                        np.array(self._lines_dataset['P2'], dtype=np.float64),
                                        np.array(self._lines_dataset['P3'], dtype=np.float64))).transpose()

    def _check_types(self, f107):
        if isinstance(f107, (float, int, np.integer, list, np.ndarray)):
            if isinstance(f107, (list, np.ndarray)):
                if not all([isinstance(x, (float, int, np.integer,)) for x in f107]):
                    raise TypeError(
                        f'Only float and int types are allowed in array.')
        else:
            raise TypeError(f'Only float, int, list and np.ndarray types are allowed. f107 was {type(f107)}')
        return True

    def _get_f107(self, f107):
        try:
            if isinstance(f107, float) or isinstance(f107, int):
                return np.array([f107 ** 2, f107, 1], dtype=np.float64).reshape(1, 3)
            return np.vstack([np.array([x ** 2, x, 1]) for x in f107], dtype=np.float64)
        except TypeError:
            raise TypeError('Only int, float or array-like object types are allowed')

    def _predict(self, matrix_a, vector_x):
        return np.dot(matrix_a, vector_x)

    def get_spectral_lines(self, f107):
        if self._check_types(f107):
            F107 = self._get_f107(f107)

        res = self._predict(self._lines_coeffs, F107.T)
        return xr.Dataset(data_vars={'euv_flux_spectra': (('line_wavelength', 'F107'), res),
                                     'wavelength': ('line_number', self._lines_dataset['lambda'].values)},
                          coords={'F107': F107[:, 1],
                                  'line_wavelength': self._lines_dataset['lambda'].values,
                                  'line_number': np.arange(17)},
                          attrs={'F10.7 units': '10^-22 · W · m^-2 · Hz^-1',
                                 'spectra units': 'W · m^-2 · nm^-1',
                                 'wavelength units': 'nm',
                                 'euv_flux_spectra': 'modeled EUV solar irradiance',
                                 'wavelength': 'the wavelength of a discrete line'})

    def get_spectral_bands(self, f107):
        if self._check_types(f107):
            F107 = self._get_f107(f107)

        res = self._predict(self._bands_coeffs, F107.T)
        return xr.Dataset(data_vars={'euv_flux_spectra': (('band_center', 'F107'), res),
                                     'lband': ('band_number', self._bands_dataset['lband'].values),
                                     'uband': ('band_number', self._bands_dataset['uband'].values)},
                          coords={'F107': F107[:, 1],
                                  'band_center': self._bands_dataset['center'].values,
                                  'band_number': np.arange(20)},
                          attrs={'F10.7 units': '10^-22 · W · m^-2 · Hz^-1',
                                 'spectra units': 'W · m^-2 · nm^-1',
                                 'wavelength units': 'nm',
                                 'euv_flux_spectra': 'modeled EUV solar irradiance',
                                 'lband': 'lower boundary of wavelength interval',
                                 'uband': 'upper boundary of wavelength interval'})

    def get_spectra(self, f107):
        return self.get_spectral_bands(f107), self.get_spectral_lines(f107)

    def predict(self, f107):
        if self._check_types(f107):
            F107 = self._get_f107(f107)

        res = self._predict(self._full_coeffs, F107.T)
        return xr.Dataset(data_vars={'euv_flux_spectra': (('band_center', 'F107'), res),
                                     'lband': ('band_number', self._full_dataset['lband'].values),
                                     'uband': ('band_number', self._full_dataset['uband'].values)},
                          coords={'F107': F107[:, 1],
                                  'band_center': self._full_dataset['center'].values,
                                  'band_number': np.arange(37)},
                          attrs={'F10.7 units': '10^-22 · W · m^-2 · Hz^-1',
                                 'spectra units': 'W · m^-2 · nm^-1',
                                 'wavelength units': 'nm',
                                 'euv_flux_spectra': 'modeled EUV solar irradiance',
                                 'lband': 'lower boundary of wavelength interval',
                                 'uband': 'upper boundary of wavelength interval'})
