"""Material model module."""

from pydantic import BaseModel
import csv


class Material(BaseModel):
    id: int | None = None
    name: str
    category: str
    conductivity_w_mk: float
    emissivity: float
    density_kg_m3: float
    spec_heat_cap_J_kgK: float
    roughness: str
    thermal_absorptance: float
    solar_absorptance: float
    visible_absorptance: float
    color: str
    source: str
    notes: str

    def attribute_by_alias(self, _attr_name: str):
        """Return the attribute value by an alias name. ie: "Name">obj.name"""

        aliases = {
            "Category": "category",
            "Conductivity": "conductivity_w_mk",
            "Emissivity": "emissivity",
            "Density": "density_kg_m3",
            "Spec Heat Cap": "spec_heat_cap_J_kgK",
            "Roughness": "roughness",
            "Thermal Absorptance": "thermal_absorptance",
            "Solar Absorptance": "solar_absorptance",
            "Visible Absorptance": "visible_absorptance",
            "Color": "color",
            "Source": "source",
            "Notes": "notes",
        }

        return getattr(self, aliases[_attr_name], "")

    class Config:
        from_attributes = True


def load_models_from_air_table_csv(_csv_file_path) -> list[Material]:
    """Used to load in material records from AirTable CSV export."""
    materials = []
    with open(_csv_file_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            materials.append(
                Material(
                    name=row["\ufeffname"],
                    category=row["category"],
                    conductivity_w_mk=float(row["conductivity_w_mk"]),
                    emissivity=float(row["emissivity"]),
                    density_kg_m3=0,
                    spec_heat_cap_J_kgK=0,
                    roughness="Rough",
                    thermal_absorptance=0,
                    solar_absorptance=0,
                    visible_absorptance=0,
                    color=row["ARGB_COLOR"],
                    source=row["source"],
                    notes=row["comments"],
                )
            )
    return materials


from io import StringIO


def dump_material_records_to_csv(materials: list[Material]):
    """Write the material records out to a CSV string which can be written to file."""

    output = StringIO()
    headers = list(Material.model_fields.keys())
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for material in materials:
        writer.writerow(material.model_dump())

    csv_string = output.getvalue()
    output.close()
    return csv_string


def load_material_records_from_csv(_csv_file_path) -> list[Material]:
    """Load the material records from a CSV file."""
    materials = []
    with open(_csv_file_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            materials.append(Material.model_validate(row))

    return materials
