"""View: Table used to display the list of Materials"""

import fasthtml.common as fhc

from src.model.material import Material

# TODO: Add filtering by category

COLUMN_ORDER = [
    "Category",
    "Conductivity",
    "Emissivity",
    "Density",
    "Spec Heat Cap",
    "Roughness",
    "Thermal Absorptance",
    "Solar Absorptance",
    "Visible Absorptance",
    "Color",
    "Source",
    "Notes",
]


class Header:

    @staticmethod
    def left():
        return fhc.Div(fhc.Div("Material", cls="cell-header"), cls="left-row-header")

    @staticmethod
    def right():
        return fhc.Div(
            *(fhc.Div(_, cls="cell-header") for _ in COLUMN_ORDER),
            cls="right-row-header",
        )


class Footer:

    @staticmethod
    def add_material_button():
        return fhc.Button(
            "New Material",
            cls="control-button",
            hx_get="/add",
            hx_target="#main",
        )

    @staticmethod
    def left():
        return fhc.Div(Footer.add_material_button(), cls="left-row-footer")

    @staticmethod
    def right():
        return fhc.Div(cls="right-row-footer")


class Rows:

    @staticmethod
    def delete_button(material: Material):
        return fhc.Div(
            fhc.Button(
                "Delete",
                cls="control-button",
                hx_post=f"/delete/{material.id}",
                hx_target="#main",
            ),
            cls="cell-control",
        )

    @staticmethod
    def edit_button(material: Material):
        return fhc.Div(
            fhc.Button("Edit", cls="control-button"),
            cls="cell-control",
            hx_get=f"/edit/{material.id}",
            hx_target="#main",
        )

    @staticmethod
    def create_row_left(material: Material):
        return fhc.Div(
            Rows.delete_button(material),
            Rows.edit_button(material),
            fhc.Div(material.name, cls="cell-data"),
            cls="left-row",
        )

    @staticmethod
    def create_row_right(material: Material):
        row_values = (
            fhc.Div(material.attribute_by_alias(col_name), cls="cell-data")
            for col_name in COLUMN_ORDER
        )
        return fhc.Div(*row_values, cls="right-row")

    @staticmethod
    def left(materials: list[Material]):
        return fhc.Div(
            *[Rows.create_row_left(m) for m in materials],
            cls="left-data",
            id="left-rows",
            hx_swap_oob="true",
        )

    @staticmethod
    def right(materials: list[Material]):
        return fhc.Div(
            *[Rows.create_row_right(m) for m in materials],
            cls="right-data",
            id="right-rows",
            hx_swap_oob="true",
        )


class Filter:

    @staticmethod
    def left():
        return fhc.Div(cls="filter-left")

    @staticmethod
    def right(categories):
        return fhc.Form(
            hx_post="/filter_by_category",
            hx_trigger="change from:#category-filter, keyup delay:500ms from:#html",
        )(
            fhc.Select(
                fhc.Option("-", value="-"),
                *[fhc.Option(c, value=c) for c in categories],
                cls="filter-dropdown",
                id="category-filter",
            )
        )


class Table:

    @staticmethod
    def categories(materials: list[Material]) -> list[str]:
        return sorted(set(m.category for m in materials))

    @staticmethod
    def left_column(materials: list[Material]):
        return fhc.Div(
            Header.left(),
            Filter.left(),
            Rows.left(materials),
            Footer.left(),
            cls="column left-column",
        )

    @staticmethod
    def right_column(materials: list[Material]):
        return fhc.Div(
            Header.right(),
            Filter.right(Table.categories(materials)),
            Rows.right(materials),
            Footer.right(),
            cls="column right-column",
        )

    @staticmethod
    def render(materials: list[Material]):
        """fastHTML render function."""
        print(f"Rendering {len(materials)} materials.")
        return fhc.Div(
            Table.left_column(materials),
            Table.right_column(materials),
            cls="table",
        )
