from typing import Any
import fasthtml.common as fhc
from starlette.responses import RedirectResponse
from starlette.datastructures import UploadFile
from pydantic import ValidationError

from src.schemas.base import get_session
from src.schemas.material import MaterialDB
from src.model.material import (
    Material,
    load_material_records_from_csv,
    dump_material_records_to_csv,
)
from src.views.table import Table
from src.views.material_details import MaterialDetails
from src.views.menu import Menu


def register_routes(rt):

    @rt("/")
    async def get():
        """Main page to display all of the Materials."""

        with get_session() as session:
            materials = (
                session.query(MaterialDB)
                .order_by(MaterialDB.category, MaterialDB.name)
                .all()
            )

        return fhc.Titled(
            "Materials List",
            Menu(),
            Table(
                sorted(
                    [Material.model_validate(m) for m in materials],
                    key=lambda x: (x.category, x.name),
                )
            ),
            id="main",
        )

    @rt("/add", methods=["GET", "POST"])
    async def add(req: fhc.Request):
        """Add a new Material to the Database."""

        if req.method == "POST":
            form_data = await req.form()
            form_data = dict(form_data)
            try:
                material_data = Material.model_validate(form_data)
            except ValidationError as e:
                return fhc.Titled(
                    "Add New Material",
                    MaterialDetails(),
                    fhc.Div(str(e), cls="error-message"),
                )
            with get_session() as session:
                new_material = MaterialDB(**material_data.model_dump())
                session.add(new_material)
                session.commit()
            return RedirectResponse("/", status_code=303)

        return fhc.Titled("Add New Material", MaterialDetails())

    async def get_file_from_form(req: fhc.Request) -> RedirectResponse | UploadFile:
        """Get a File from Form data (upload)."""

        form = await req.form()

        if not (file := form.get("file")):
            return RedirectResponse("/", status_code=303)
        if not isinstance(file, UploadFile):
            return RedirectResponse("/", status_code=303)

        return file

    @rt("/add_materials_from_csv", methods=["POST"])
    async def add_materials_from_csv(req: fhc.Request):
        """Load in materials from an uploaded CSV file."""

        if isinstance(file := await get_file_from_form(req), RedirectResponse):
            return file

        file_path = f"/tmp/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        materials = load_material_records_from_csv(file_path)

        with get_session() as session:
            for material in materials:
                existing_material = (
                    session.query(MaterialDB)
                    .filter(MaterialDB.id == material.id)
                    .first()
                )
                if existing_material:
                    for key, value in material.model_dump().items():
                        setattr(existing_material, key, value)
                else:
                    new_material = MaterialDB(**material.model_dump())
                    session.add(new_material)
            session.commit()

        return RedirectResponse("/", status_code=303)

    @rt("/save_to_csv", methods=["GET"])
    async def save_to_csv():
        """Save material records to a CSV file."""

        with get_session() as session:
            materials = session.query(MaterialDB).all()

        materials_pydantic = [Material.model_validate(m) for m in materials]
        content = dump_material_records_to_csv(materials_pydantic)
        filename = "materials.csv"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/plain",
        }

        return fhc.Response(content, headers=headers)

    @rt("/delete/{material_id}", methods=["POST"])
    async def delete(material_id: int):
        """Delete a Material from the Database."""

        with get_session() as session:
            material = (
                session.query(MaterialDB).filter(MaterialDB.id == material_id).first()
            )
            if material:
                session.delete(material)
                session.commit()

        return RedirectResponse("/", status_code=303)

    @rt("/edit/{material_id}", methods=["GET", "POST"])
    async def edit(req: fhc.Request, material_id: int):
        """Edit a Material in the Database."""
        with get_session() as session:
            material = (
                session.query(MaterialDB).filter(MaterialDB.id == material_id).first()
            )
            if not material:
                return RedirectResponse("/", status_code=303)
            if req.method == "POST":
                form_data = await req.form()
                form_data_dict: dict[str, Any] = dict(form_data)
                form_data_dict["id"] = material_id
                try:
                    material_data = Material.model_validate(form_data_dict)
                except ValidationError as e:
                    return fhc.Titled(
                        "Edit Material",
                        MaterialDetails(material),
                        fhc.Div(str(e), cls="error-message"),
                    )
                for key, value in material_data.model_dump().items():
                    setattr(material, key, value)
                session.commit()
                return RedirectResponse("/", status_code=303)

        return fhc.Titled("Edit Material", MaterialDetails(material))

    @rt("/filter/{d}", methods=["POST"])
    async def filter(d: dict):
        print(f"{d=}")
        if not (filter := d.get("category-filter", None)):
            return RedirectResponse("/", status_code=303)

        if filter == "-":
            return RedirectResponse("/", status_code=303)

        with get_session() as session:
            materials = (
                session.query(MaterialDB)
                .filter(MaterialDB.category == filter)
                .order_by(MaterialDB.category, MaterialDB.name)
                .all()
            )

        return fhc.Titled(
            "Materials List",
            Menu(),
            Table(
                sorted(
                    [Material.model_validate(m) for m in materials],
                    key=lambda x: (x.category, x.name),
                )
            ),
            id="main",
        )
