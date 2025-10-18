# GLASS extension for loading PKDGRAV simulations

This repository contains a GLASS extension for loading PKDGRAV simulations such
as the Gower St simulations.

## Installation

Install the package with pip into your GLASS environment:

    pip install glass.ext.pkdgrav

## Quick start

Load a PKDGRAV simulation by pointing the `glass.ext.pkdgrav.load()` function
to the simulation's `.par` file:

```py
sim = glass.ext.pkdgrav.load("gowerst/run014/control.par")
```

The resulting object has attributes such as `sim.parameters`, `sim.cosmology`,
and `sim.shells` that describe the simulation.

The matter shells can be read with the simulation-specific functions such as
`glass.ext.pkdgrav.read_gowerst(sim)`.

## Cosmology

The simulation cosmology is returned from the stored input file. No new
cosmological quantities are computed.

The returned cosmology object follows the Cosmology API standard. It can be
passed directly into GLASS functions that require it.

## Example

```py
import glass
import glass.ext.pkdgrav

# load simulation
sim = glass.ext.pkdgrav.load("gowerst/run014/control.par")

# get simulation parameters
cosmo = sim.cosmology
shells = sim.shells

# nside for computation; could be sim.nside
nside = 1024

# more setup
...

# this will load a GowerSt simulation iteratively
# up to redshift 2 and rescaled to nside
matter = glass.ext.pkdgrav.read_gowerst(sim, zmax=2.0, nside=nside)

# this will compute the convergence field iteratively
convergence = glass.MultiPlaneConvergence(cosmo)

# load each delta map and process
for i, delta in enumerate(matter):

    # add lensing plane from the window function of this shell
    convergence.add_window(delta, shells[i])

    # process shell
    ...

```
