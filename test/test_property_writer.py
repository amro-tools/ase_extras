from ase_extras.property_writer import PropertyWriter

from ase.io import read
from ase.units import fs
from ase.md.langevin import Langevin
from ase.constraints import FixBondLengths
from pathlib import Path
import json

import numpy as np


def constrain_water(atoms):
    n_atoms = len(atoms)
    n_molecules = int(n_atoms / 3)

    pairs = []
    for i_molecule in range(n_molecules):
        iO = 3 * i_molecule
        iH1 = iO + 1
        iH2 = iO + 2

        pairs.append([iO, iH1])
        pairs.append([iO, iH2])
        pairs.append([iH1, iH2])

    atoms.set_constraint(FixBondLengths(pairs, tolerance=1e-5))


def construct_calculator(atoms):
    from ase.calculators.tip4p import TIP4P

    return TIP4P()


def test_property_writer():
    n_iter = 3
    input_xyz = Path(__file__).parent / "resources/system.xyz"
    temperature = 300
    logfile = "log.txt"
    friction = 0.5

    # Read the system using ASE
    with open(input_xyz, "r") as f:
        atoms = read(f, format="xyz")

    atoms.set_cell([20.0, 20.0, 20.0])
    atoms.calc = construct_calculator(atoms)

    dt = 1 * fs

    dyn = Langevin(
        atoms,
        timestep=dt,
        temperature_K=temperature,
        friction=friction,
        logfile=logfile,
    )

    writer = PropertyWriter(
        atoms,
        properties=["energy", "temperature", "total_energy", "kinetic_energy"],
        file="properties.csv",
    )

    dyn.attach(writer.log, interval=1)
    dyn.attach(writer.log_to_file, interval=1)

    constrain_water(atoms)
    dyn.run(steps=n_iter)
    dyn.close()

    writer.save_to_json("properties.json")

    temperature_fin = atoms.get_temperature()
    total_energy = atoms.get_total_energy()
    kinetic_energy = atoms.get_kinetic_energy()
    potential_energy = atoms.get_potential_energy()

    with open("properties.json", "r") as f:
        from_json = json.load(f)

    assert np.isclose(from_json["temperature"][-1], temperature_fin)
    assert np.isclose(from_json["potential_energy"][-1], potential_energy)
    assert np.isclose(from_json["total_energy"][-1], total_energy)
    assert np.isclose(from_json["kinetic_energy"][-1], kinetic_energy)


if __name__ == "__main__ ":
    test_property_writer()
