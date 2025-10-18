import os

import healpy as hp
import numpy as np


def resample(n, nside):
    # keep the number of particles constant
    ntot = n.sum()
    n = hp.ud_grade(n, nside, power=-2)
    assert n.sum() == ntot, "resampling lost particles!"
    return n


def read_gowerst(sim, dir=None, *, zmax=None, nside=None, raw=False):
    if dir is None:
        dir = sim.dir

    outname = sim.parameters["achOutName"]
    steps = range(sim.parameters["nSteps"], 0, -1)
    for shell, step in zip(sim.shells, steps):
        if zmax is not None and zmax < shell.za.min():
            break

        tag = "lightcone" if step > 1 else "incomplete"
        path = os.path.join(dir, f"{outname}.{step:05d}.{tag}.npy")
        n = np.load(path)

        if nside is not None and nside != hp.get_nside(n):
            n = resample(n, nside)

        if raw:
            yield n
        else:
            nbar = n.mean()
            yield n / nbar - 1.0
