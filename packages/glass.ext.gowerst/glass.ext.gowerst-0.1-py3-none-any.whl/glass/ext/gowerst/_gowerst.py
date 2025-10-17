import dataclasses
import os

import healpy as hp
import numpy as np

import glass

from ._cosmology import Cosmology
from ._parfile import read_par


@dataclasses.dataclass
class Simulation:
    path: str | os.PathLike[str]
    dir: str | os.PathLike[str] | None = None

    parameters: dict[str, object] = dataclasses.field(init=False, repr=False)
    cosmology: dict[str, object] = dataclasses.field(init=False, repr=False)

    nside: int | None = dataclasses.field(init=False, repr=False)

    steps: list[int] = dataclasses.field(init=False, repr=False)
    shells: list[glass.RadialWindow] = dataclasses.field(init=False, repr=False)

    def __post_init__(self):
        self.path = os.path.realpath(os.path.expanduser(self.path))

        if self.dir is None:
            self.dir = os.path.dirname(self.path)

        self.parameters = read_par(self.path)

        if not self.parameters.get("bClass", False):
            raise ValueError("simulations with simple cosmology not supported")

        class_path = self.parameters["achClassFilename"]
        if not os.path.isabs(class_path):
            class_path = os.path.join(self.dir, class_path)
        self.cosmology = Cosmology(class_path)

        self.nside = self.parameters.get("nSideHealpix")

        z_values = np.genfromtxt(
            os.path.join(self.dir, "z_values.txt"),
            delimiter=",",
            names=True,
        )

        self.shells = []
        for step in range(self.parameters["nSteps"], 0, -1):
            (found,) = np.where(z_values["Step"] == step)
            if len(found) != 1:
                raise ValueError(
                    f"z_values.txt does not contain step {step}, inconsistent .par file?"
                )
            row = z_values[found[0]]
            z_near, z_far = row[["z_near", "z_far"]]
            shell = glass.RadialWindow(
                za=np.linspace(z_near, z_far, 100),
                wa=np.ones(100),
            )
            self.shells.append(shell)

    def lightcone(self, zmax=None, nside=None, raw=False):
        outname = self.parameters["achOutName"]
        steps = range(self.parameters["nSteps"], 0, -1)
        for shell, step in zip(self.shells, steps):
            if zmax is not None and zmax < shell.za.min():
                break

            tag = "lightcone" if step > 1 else "incomplete"
            path = os.path.join(self.dir, f"{outname}.{step:05d}.{tag}.npy")

            n = np.load(path)
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


def load(path: str | os.PathLike[str]) -> Simulation:
    return Simulation(path)
