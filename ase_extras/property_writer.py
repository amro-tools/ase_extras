import json
from typing import Optional
from pathlib import Path
from ase import Atoms
from ase.optimize.optimize import Dynamics
from typing import Callable, Any
import warnings


class PropertyWriter:
    def __init__(
        self,
        atoms: Atoms,
        properties: list[str] = [""],
        callback_properties: Optional[
            list[tuple[str, Callable[[Atoms, Dynamics], Any]]]
        ] = None,
        file: Optional[Path] = None,
        dyn: Optional[Dynamics] = None,
    ):
        self.atoms = atoms
        self.record = dict()
        self.properties = properties
        self.file = file
        self.dyn = dyn

        self.callback_properties = self._create_callbacks()

        if not callback_properties is None:
            self.callback_properties += callback_properties

        self.record_keys = self.validate_keys()

        self.record = {}
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

    def validate_keys(self):
        """Make sure you don't have duplicate keys (multiple keys in properties, callback_properties or keys in both)

        Raises:
            Exception: If you have duplicate keys
        """
        keys = []
        for property_name, callback in self.callback_properties:
            keys.append(property_name)
        record_keys_unique = set(keys)
        if len(record_keys_unique) != len(keys):
            raise Exception(
                "Duplicate keys. You cannot have the same key inside properties and callback_properties or in properties."
            )
        return keys

    def _create_callbacks(self):
        # creates predefined callbacks for each property in properties
        callback_properties = []

        for p in self.properties:
            if p == "total_energy":

                def callback(atoms, dyn):
                    kin_energy = atoms.get_kinetic_energy()
                    pot_energy = atoms.calc.results["energy"]
                    return pot_energy + kin_energy

                callback_properties.append((p, callback))

            elif p == "kinetic_energy":

                def callback(atoms, dyn):
                    kin_energy = atoms.get_kinetic_energy()
                    return kin_energy

                callback_properties.append((p, callback))

            elif p == "temperature":

                def callback(atoms, dyn):
                    return atoms.get_temperature()

                callback_properties.append((p, callback))

            elif p == "potential_energy":

                def callback(atoms, dyn):
                    return atoms.calc.results["energy"]

                callback_properties.append((p, callback))

            elif p == "nsteps":

                def callback(atoms, dyn):
                    return dyn.nsteps

                callback_properties.append((p, callback))
            else:
                raise Exception(
                    f"{p} does not have a predefined callback. You cannot put it inside properties but you may define a custom callback and put it in callback_properties"
                )

        return callback_properties

    def get_property(self):
        results = {}
        for property_name, callback in self.callback_properties:
            try:
                results[property_name] = callback(self.atoms, self.dyn)
            except:
                results[property_name] = float("nan")
                warnings.warn(
                    f"Error when computing property {property_name}. Setting to nan"
                )
        return results

    def save_to_json(self, file: Path):
        with open(file, "w") as f:
            json.dump(self.record, f, indent=4)
