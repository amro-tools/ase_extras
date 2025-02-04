import json
from typing import Optional
from pathlib import Path
from ase import Atoms


class PropertyWriter:
    def __init__(
        self, atoms: Atoms, properties: list[str] = [""], file: Optional[Path] = None
    ):
        self.atoms = atoms
        self.record = dict()
        self.properties = properties
        self.file = file

        for p in properties:
            self.record[p] = []

    def log(self):
        for p in self.properties:
            if p == "total_energy":
                kin_energy = self.atoms.get_kinetic_energy()
                pot_energy = self.atoms.calc.results["energy"]
                self.record[p].append(kin_energy + pot_energy)
            elif p == "kinetic_energy":
                kin_energy = self.atoms.get_kinetic_energy()
                self.record[p].append(kin_energy)
            elif p == "temperature":
                temp = self.atoms.get_temperature()
                self.record[p].append(temp)
            elif p == "potential_energy" or "energy":
                pot_energy = self.atoms.calc.results["energy"]
                self.record["potential_energy"].append(pot_energy)
            else:
                try:
                    r = self.atoms.calc.results[p]
                    self.record[p].append(r)
                except:
                    print(f"Calculator does not have property {p}")

    def save(self, file: Path):
        with open(file, "w") as f:
            json.dump(self.record, f, indent=4)

    def __del__(self):
        if not self.file is None:
            self.save(self.file)
