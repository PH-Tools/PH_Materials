from typing import Any
import fasthtml.common as fhc
from starlette.responses import RedirectResponse
from pydantic import ValidationError

from src.schemas.base import Base, engine, SessionLocal
from src.schemas.material import MaterialDB
from src.model.material import Material

# Create the Database tables
Base.metadata.create_all(bind=engine)


# FastHTML app setup
app, rt = fhc.fast_app(
    hdrs=(
        fhc.Link(rel="stylesheet", href="src/static/table.css", type="text/css"),
        fhc.Link(
            rel="stylesheet", href="src/static/edit_material.css", type="text/css"
        ),
    ),
)


def create_control_buttons(material: MaterialDB):
    return (
        fhc.Div(
            fhc.Div(
                fhc.Button(
                    "Delete",
                    klass="control-button",
                    hx_post=f"/delete/{material.id}",
                    hx_target="main",
                ),
                klass="cell-control",
            ),
            fhc.Div(
                fhc.Button("Edit", klass="control-button"),
                klass="cell-control",
                hx_get=f"/edit/{material.id}",
                hx_target="main",
            ),
            klass="row-control",
        ),
    )


def create_row(material: MaterialDB):
    return fhc.Div(
        create_control_buttons(material),
        fhc.Div(
            fhc.Div(material.name, klass="cell-data"),
            fhc.Div(material.category, klass="cell-data"),
            fhc.Div(material.conductivity_w_mk, klass="cell-data"),
            fhc.Div(material.emissivity, klass="cell-data"),
            fhc.Div(material.density_kg_m3, klass="cell-data"),
            fhc.Div(material.spec_heat_cap_J_kgK, klass="cell-data"),
            fhc.Div(material.roughness, klass="cell-data"),
            fhc.Div(material.thermal_absorptance, klass="cell-data"),
            fhc.Div(material.solar_absorptance, klass="cell-data"),
            fhc.Div(material.visible_absorptance, klass="cell-data"),
            fhc.Div(material.color, klass="cell-data"),
            fhc.Div(material.source, klass="cell-data"),
            fhc.Div(material.notes, klass="cell-data"),
            klass="row-data",
        ),
        klass="row",
    )


def create_table(materials: list[MaterialDB]):
    header = fhc.Div(
        fhc.Div(
            fhc.Div("", klass="cell-control"),
            klass="row-control",
        ),
        fhc.Div(
            fhc.Div("Name", klass="cell-data"),
            fhc.Div("Category", klass="cell-data"),
            fhc.Div("Conductivity", klass="cell-data"),
            fhc.Div("Emissivity", klass="cell-data"),
            fhc.Div("Density", klass="cell-data"),
            fhc.Div("Spec Heat Cap", klass="cell-data"),
            fhc.Div("Roughness", klass="cell-data"),
            fhc.Div("Thermal Absorptance", klass="cell-data"),
            fhc.Div("Solar Absorptance", klass="cell-data"),
            fhc.Div("Visible Absorptance", klass="cell-data"),
            fhc.Div("Color", klass="cell-data"),
            fhc.Div("Source", klass="cell-data"),
            fhc.Div("Notes", klass="cell-data"),
            klass="row-data",
        ),
        klass="row",
    )
    rows = [create_row(m) for m in materials]
    rows.append(
        fhc.Div(
            fhc.Div(
                fhc.Div(
                    fhc.Button(
                        "New Material",
                        klass="control-button",
                        hx_get="/add",
                        hx_target="main",
                    ),
                    klass="cell-control",
                ),
                klass="row-control",
            ),
            fhc.Div(fhc.Div("", klass="cell-data"), klass="row-data"),
            klass="row",
        )
    )
    return fhc.Div(header, *rows, id="table")


def material_attribute_input(
    material: MaterialDB | None,
    attribute_name: str,
    default_value: str | int | float,
    display_name: str,
):
    if not material:
        value = default_value
    else:
        value = getattr(material, attribute_name, default_value)

    return (
        fhc.Label(f"{display_name}:", klass="material-attribute-label"),
        fhc.Input(
            name=attribute_name,
            value=value,
            placeholder=attribute_name,
            klass="material-attribute-input",
        ),
    )


def material_details(material: MaterialDB | None = None):
    return fhc.Form(
        fhc.Div(
            material_attribute_input(material, "name", "...", "Name"),
            material_attribute_input(material, "category", "...", "Category"),
            material_attribute_input(material, "conductivity_w_mk", 1, "Conductivity"),
            material_attribute_input(material, "emissivity", 0.9, "Emissivity"),
            material_attribute_input(material, "density_kg_m3", 1, "Density"),
            material_attribute_input(
                material, "spec_heat_cap_J_kgK", 1, "Spec. Heat Cap."
            ),
            material_attribute_input(material, "roughness", "Rough", "Roughness"),
            material_attribute_input(
                material, "thermal_absorptance", 0.9, "Thermal Abs."
            ),
            material_attribute_input(material, "solar_absorptance", 0.9, "Solar Abs."),
            material_attribute_input(
                material, "visible_absorptance", 0.9, "Visible Abs."
            ),
            material_attribute_input(material, "color", "...", "Color"),
            material_attribute_input(material, "source", "...", "Source"),
            material_attribute_input(material, "notes", "...", "Notes"),
            klass="material-details",
        ),
        fhc.Div(
            fhc.Button(
                "Cancel",
                type="button",
                hx_get="/",
                hx_target="main",
                klass="material-edit-form-button",
            ),
            fhc.Button("Save", type="submit", klass="material-edit-form-button"),
            klass="material-edit-form-buttons",
        ),
        method="post",
        action=f"/edit/{material.id}" if material else "/add",
        klass="material-edit-form",
    )


@rt("/")
async def get():
    session = SessionLocal()
    materials = session.query(MaterialDB).all()
    session.close()
    return fhc.Titled(
        "Materials List",
        create_table(materials),
        id="main",
    )


def get_clean_data(input, attribute: str, _type):
    return _type(str(input.get(attribute, "")).strip())


@rt("/add", methods=["GET", "POST"])
async def add(req: fhc.Request):
    if req.method == "POST":
        form_data = await req.form()
        form_data = dict(form_data)
        try:
            material_data = Material.model_validate(form_data)
        except ValidationError as e:
            return fhc.Titled(
                "Add New Material",
                material_details(),
                fhc.Div(str(e), klass="error-message"),
            )

        session = SessionLocal()
        new_material = MaterialDB(
            name=material_data.name,
            category=material_data.category,
            conductivity_w_mk=material_data.conductivity_w_mk,
            emissivity=material_data.emissivity,
            density_kg_m3=material_data.density_kg_m3,
            spec_heat_cap_J_kgK=material_data.spec_heat_cap_J_kgK,
            roughness=material_data.roughness,
            thermal_absorptance=material_data.thermal_absorptance,
            solar_absorptance=material_data.solar_absorptance,
            visible_absorptance=material_data.visible_absorptance,
            color=material_data.color,
            source=material_data.source,
            notes=material_data.notes,
        )
        session.add(new_material)
        session.commit()
        session.close()
        return RedirectResponse("/", status_code=303)

    return fhc.Titled("Add New Material", material_details())


@rt("/delete/{material_id}", methods=["POST"])
async def delete(material_id: int):
    session = SessionLocal()
    material = session.query(MaterialDB).filter(MaterialDB.id == material_id).first()
    if material:
        session.delete(material)
        session.commit()
    session.close()
    return RedirectResponse("/", status_code=303)


@rt("/edit/{material_id}", methods=["GET", "POST"])
async def edit(req: fhc.Request, material_id: int):
    session = SessionLocal()
    material = session.query(MaterialDB).filter(MaterialDB.id == material_id).first()

    if not material:
        session.close()
        return RedirectResponse("/", status_code=303)

    if req.method == "POST":
        form_data = await req.form()
        form_data_dict: dict[str, Any] = dict(form_data)
        form_data_dict["id"] = material_id
        try:
            material_data = Material.model_validate(form_data_dict)
        except ValidationError as e:
            session.close()
            return fhc.Titled(
                "Edit Material",
                material_details(material),
                fhc.Div(str(e), klass="error-message"),
            )

        material.name = material_data.name
        material.category = material_data.category
        material.conductivity_w_mk = material_data.conductivity_w_mk
        material.emissivity = material_data.emissivity
        material.density_kg_m3 = material_data.density_kg_m3
        material.spec_heat_cap_J_kgK = material_data.spec_heat_cap_J_kgK
        material.roughness = material_data.roughness
        material.thermal_absorptance = material_data.thermal_absorptance
        material.solar_absorptance = material_data.solar_absorptance
        material.visible_absorptance = material_data.visible_absorptance
        material.color = material_data.color
        material.source = material_data.source
        material.notes = material_data.notes

        session.commit()
        session.close()
        return RedirectResponse("/", status_code=303)

    session.close()
    return fhc.Titled("Edit Material", material_details(material))


fhc.serve()
