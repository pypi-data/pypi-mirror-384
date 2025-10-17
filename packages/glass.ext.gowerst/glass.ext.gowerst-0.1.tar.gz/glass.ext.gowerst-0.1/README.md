# GLASS extension for loading Gower St simulations

This repository contains a GLASS extension for loading Gower St simulations.

## Installation

Install the package with pip into your GLASS environment:

    pip install glass.ext.gowerst

## Quick start

Load a GowerSt simulation by pointing the `glass.ext.gowerst.load()` function
to the simulation's `.par` file:

```py
sim = glass.ext.gowerst.load("~/data/gowerst/run014/control.par")
```

The resulting object has attributes such as `sim.parameters`, `sim.cosmology`,
and `sim.shells` that describe the simulation.

The matter shells can be loaded with the `sim.lightcone()` function.

## Cosmology

The simulation cosmology is returned from the stored input file. No new
cosmological quantities are computed.

The returned cosmology object follows the Cosmology API standard. It can be
passed directly into GLASS functions that require it.

## Example

```py
import glass
import glass.ext.gowerst

# load simulation
sim = glass.ext.gowerst.load("gowerst/run014/control.par")

# get simulation parameters
cosmo = sim.cosmology
shells = sim.shells

# nside for computation; could be sim.nside
nside = 1024

# more setup
...

# this will load the lightcone iteratively
# up to redshift 2 and rescaled to nside
matter = sim.lightcone(zmax=2.0, nside=nside)

# this will compute the convergence field iteratively
convergence = glass.MultiPlaneConvergence(cosmo)

# load each delta map and process
for i, delta in enumerate(matter):

    # add lensing plane from the window function of this shell
    convergence.add_window(delta, shells[i])

    # process shell
    ...

```
