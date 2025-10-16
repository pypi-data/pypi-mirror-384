# ACID/cli.py
import argparse
import numpy as np
from astropy.io import fits
import multiprocessing as mp

from . import ACID as acid_mod  # imports ACID/ACID.py module

def cli():
    p = argparse.ArgumentParser(
        description="Run ACID (LSD + continuum fit) from the command line."
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--fits", help="Path to FITS with HDUs: 0=wavelength, 1=flux, 2=error, 3=S/N")
    group.add_argument("--harps-list", nargs="+", help="List of HARPS files (same night)")

    p.add_argument("--linelist", required=True, help="Path to VALD linelist")
    p.add_argument("--vmin", type=float, default=-25.0)
    p.add_argument("--vmax", type=float, default=25.0)
    p.add_argument("--deltav", type=float, default=0.82)
    p.add_argument("--nsteps", type=int, default=4000)
    p.add_argument("--parallel", action="store_true", help="Use multiprocessing in MCMC")
    p.add_argument("--cores", type=int, default=None, help="Number of cores if --parallel")
    p.add_argument("--poly-order", type=int, default=3)
    p.add_argument("--pix-chunk", type=int, default=20)
    p.add_argument("--dev-perc", type=int, default=25)
    p.add_argument("--n-sig", type=int, default=1)
    p.add_argument("--out", default="acid_profile.npz", help="Output .npz path")

    args = p.parse_args()

    # Safe on macOS/Windows for spawn; harmless if already set
    try:
        mp.set_start_method("spawn", force=True)
    except RuntimeError:
        pass

    velocities = np.arange(args.vmin, args.vmax, args.deltav)

    if args.fits:
        spec = fits.open(args.fits)
        wavelength = spec[0].data
        spectrum   = spec[1].data
        error      = spec[2].data
        sn         = spec[3].data

        result = acid_mod.ACID(
            [wavelength], [spectrum], [error], args.linelist, [sn], velocities,
            poly_or=args.poly_order, pix_chunk=args.pix_chunk, dev_perc=args.dev_perc,
            n_sig=args.n_sig, parallel=args.parallel, cores=args.cores, nsteps=args.nsteps,
            verbose=True
        )
        profile = result[0, 0, 0]
        perr    = result[0, 0, 1]
        np.savez(args.out, velocities=velocities, profile=profile, profile_error=perr)
        print(f"Saved single-profile output to {args.out}")

    else:
        BJDs, profiles, errors = acid_mod.ACID_HARPS(
            args.harps_list, args.linelist, velocities, poly_or=args.poly_order,
        )
        np.savez(args.out, BJDs=BJDs, velocities=velocities, profiles=profiles, errors=errors)
        print(f"Saved HARPS multi-order output to {args.out}")
