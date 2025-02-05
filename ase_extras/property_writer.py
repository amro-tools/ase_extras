import json
from typing import Optional
from pathlib import Path
from ase import Atoms
from ase.optimize.optimize import Dynamics


class PropertyWriter:
    def __init__(
        self,
        atoms: Atoms,
        properties: list[str] = [""],
        file: Optional[Path] = None,
        dyn: Optional[Dynamics] = None,
    ):
        self.atoms = atoms
        self.record = dict()
        self.properties = properties
        self.file = file
        self.dyn = dyn

        self.record_keys = self.get_record_keys()

        for k in self.record_keys:
            self.record[k] = []

        if not self.file is None:
            self._write_header(self.file)

    @classmethod
    def to_csv_row(cls, items: list, sep=","):
        res = ""
        for i, item in enumerate(items):
            res += str(item)
            if i != len(items) - 1:
                res += sep
        res += "\n"
        return res

    def _write_header(self, file):
        with open(file, "w") as f:
            f.write(PropertyWriter.to_csv_row(self.record_keys))

    def log(self):
        results = self.get_property()
        for p, v in results.items():
            self.record[p].append(v)

    def log_to_file(self):
        results = self.get_property()
        with open(self.file, "a") as f:
            f.write(PropertyWriter.to_csv_row(results.values()))

    def get_record_keys(self):
        keys = []
        if not self.dyn is None:
            keys.append("nsteps")

        for p in self.properties:
            if p == "energy":
                p = "potential_energy"  # Rename this
            keys.append(p)
        return keys

    def get_property(self):
        results = {}
        for p in self.record_keys:
            if p == "total_energy":
                kin_energy = self.atoms.get_kinetic_energy()
                pot_energy = self.atoms.calc.results["energy"]
                results[p] = kin_energy + pot_energy
            elif p == "kinetic_energy":
                kin_energy = self.atoms.get_kinetic_energy()
                results[p] = kin_energy
            elif p == "temperature":
                temp = self.atoms.get_temperature()
                results[p] = temp
            elif p == "potential_energy":
                pot_energy = self.atoms.calc.results["energy"]
                results["potential_energy"] = pot_energy
            elif p == "nsteps":
                results[p] = self.dyn.nsteps
            else:
                try:
                    r = self.atoms.calc.results[p]
                    results[p] = r
                except:
                    print(f"Calculator does not have property {p}")
        return results

    def save_to_json(self, file: Path):
        with open(file, "w") as f:
            json.dump(self.record, f, indent=4)
