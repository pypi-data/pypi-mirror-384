import os

import healpy as hp
import numpy as np


class NpyLoader:
    def __init__(self, sim, path):
        self.path = path
        self.outname = sim.outname

    def __call__(self, step):
        tag = "lightcone" if step > 1 else "incomplete"
        path = os.path.join(self.path, f"{self.outname}.{step:05d}.{tag}.npy")
        return np.load(path)


class ParquetLoader:
    read_parquet = None

    @classmethod
    def load(cls, path):
        if cls.read_parquet is None:
            try:
                from pandas import read_parquet
            except ModuleNotFoundError as exc:
                raise ValueError("parquet format requires pandas") from exc
            else:
                cls.read_parquet = read_parquet
        return cls.read_parquet(path)

    def __init__(self, sim, path):
        self.path = path
        self.outname = sim.outname
        self.nside = sim.nside

    def __call__(self, step):
        path = os.path.join(self.path, f"particles_{step}_{self.nside}.parquet")
        return self.load(path).to_numpy().reshape(-1)


def read_gowerst(sim, path=None, format="npy", *, zmax=None, nside=None, raw=False):
    path = os.path.expanduser(path) if path is not None else sim.dir

    if format == "npy":
        loader = NpyLoader(sim, path)
    elif format == "parquet":
        loader = ParquetLoader(sim, path)
    else:
        raise ValueError(f"unknown format: {format}")

    steps = range(sim.parameters["nSteps"], 0, -1)
    for shell, step in zip(sim.shells, steps):
        if zmax is not None and zmax < shell.za.min():
            break

        n = loader(step)

        if nside is not None and nside != hp.get_nside(n):
            # keep the number of particles constant
            ntot = n.sum()
            n = hp.ud_grade(n, nside, power=-2)
            assert n.sum() == ntot, "resampling lost particles!"

        if raw:
            yield n
        else:
            nbar = n.mean()
            yield n / nbar - 1.0
