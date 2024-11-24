"""View: MaterialDetails used when Editing and Adding Materials"""

import fasthtml.common as fhc

from src.model.material import Material


class MaterialDetails:

    def __init__(self, material: Material | None = None):
        self.material = material

    def material_attribute_input(
        self,
        attribute_name: str,
        default_value: str | int | float,
        display_name: str,
    ):
        if self.material is None:
            value = default_value
        else:
            value = getattr(self.material, attribute_name, default_value)

        return (
            fhc.Label(f"{display_name}:", klass="material-attribute-label"),
            fhc.Input(
                name=attribute_name,
                value=str(value),
                placeholder=str(value),
                klass="material-attribute-input",
            ),
        )

    def __ft__(self):
        return fhc.Form(
            fhc.Div(
                self.material_attribute_input("name", "...", "Name"),
                self.material_attribute_input("category", "...", "Category"),
                self.material_attribute_input("conductivity_w_mk", 1, "Conductivity"),
                self.material_attribute_input("emissivity", 0.9, "Emissivity"),
                self.material_attribute_input("density_kg_m3", 1, "Density"),
                self.material_attribute_input(
                    "spec_heat_cap_J_kgK", 1, "Spec. Heat Cap."
                ),
                self.material_attribute_input("roughness", "Rough", "Roughness"),
                self.material_attribute_input(
                    "thermal_absorptance", 0.9, "Thermal Abs."
                ),
                self.material_attribute_input("solar_absorptance", 0.9, "Solar Abs."),
                self.material_attribute_input(
                    "visible_absorptance", 0.9, "Visible Abs."
                ),
                self.material_attribute_input("color", "...", "Color"),
                self.material_attribute_input("source", "...", "Source"),
                self.material_attribute_input("notes", "...", "Notes"),
                cls="material-details",
            ),
            fhc.Div(
                fhc.Button(
                    "Cancel",
                    type="button",
                    hx_get="/",
                    hx_target="#main",
                    hx_swap="outerHTML",
                    cls="material-edit-form-button",
                ),
                fhc.Button("Save", type="submit", cls="material-edit-form-button"),
                cls="material-edit-form-buttons",
            ),
            method="post",
            action=f"/edit/{self.material.id}" if self.material else "/add",
            cls="material-edit-form",
        )
