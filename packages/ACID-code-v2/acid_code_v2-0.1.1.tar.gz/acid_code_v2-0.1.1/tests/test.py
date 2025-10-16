#%%
from tqdm import tqdm
import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt

a = np.array([1,2,3])
a = a.tolist()
print(isinstance(a, list))
print(a)

#%%

spec_file = fits.open('../example/sample_spec_1.fits')

wavelength = spec_file[0].data   # Wavelengths in Angstroms
spectrum = spec_file[1].data     # Spectral Flux
error = spec_file[2].data        # Spectral Flux Errors
sn = spec_file[3].data           # SN of Spectrum
print(sn)
# # choose a velocity grid for the final profile(s)
# deltav = 0.82   # velocity pixel size must not be smaller than the spectral pixel size
# velocities = np.arange(-25, 25, deltav)

# linelist = '../example/example_linelist.txt'
# linelist_expected = np.genfromtxt('%s'%linelist, skip_header=1, delimiter=',', usecols=(1,9)) # changed from skip_header=4
# wl = np.array(linelist_expected[:,0])
# d = np.array(linelist_expected[:,1])

# # wl = wl[d>0.4]
# # d = d[d>0.4]

# d = d[(wl<4100) & (wl>4000)] # only deep lines between 4000 and 4100 A
# wl = wl[(wl<4100) & (wl>4000)] # only deep lines between 4000 and 4100 A

# fig, ax = plt.subplots(figsize=(16,9))
# for wl, d in tqdm(zip(wl, d), total=len(wl)):
#     ax.plot([wl, wl], [0, -d], color='C0', alpha=0.7)
# ax.set_xlabel('Wavelength (Angstroms)')
# ax.set_ylabel('Flux')
# plt.show()


# fig, ax = plt.subplots(figsize=(16,9))
# ax.errorbar(wavelength, spectrum, yerr=error, fmt='o-', markersize=2, alpha=0.7)
# # ax.fill_between(velocities, spectrum - error, spectrum + error, alpha=0.2)
# ax.set_xlabel('Wavelength (Angstroms)')
# ax.set_ylabel('Flux')
# plt.show()

# %%
