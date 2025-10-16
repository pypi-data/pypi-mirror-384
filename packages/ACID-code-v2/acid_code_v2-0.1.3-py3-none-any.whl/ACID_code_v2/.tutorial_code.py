#%%
from astropy.io import fits
import importlib, os
import multiprocessing as mp
import ACID_code_v2 as acid
importlib.reload(acid)
import numpy as np
import matplotlib.pyplot as plt

spec_file = fits.open('../example/sample_spec_1.fits')

wavelength = spec_file[0].data   # Wavelengths in Angstroms
spectrum = spec_file[1].data     # Spectral Flux
error = spec_file[2].data        # Spectral Flux Errors
sn = spec_file[3].data           # SN of Spectrum

linelist = '../example/example_linelist.txt' # Insert path to line list

# choose a velocity grid for the final profile(s)
deltav = 0.82   # velocity pixel size must not be smaller than the spectral pixel size
velocities = np.arange(-25, 25, deltav)

# run ACID function
result = acid.ACID([wavelength], [spectrum], [error], linelist, [sn], velocities,
                   parallel=True, cores=None, nsteps=4000, verbose=True)

# extract profile and errors
profile = result[0, 0, 0]
profile_error = result[0, 0, 1]

# plot results
plt.figure()
plt.errorbar(velocities, profile, profile_error)
plt.xlabel('Velocities (km/s)')
plt.ylabel('Flux')
plt.show()