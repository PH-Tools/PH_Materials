"""View: Table used to display the list of Materials"""

from dataclasses import dataclass
import fasthtml.common as fhc

from src.model.material import Material

# TODO: Add filtering by category


@dataclass
class AttributeFilter:
    name: str
    value: str


class Header:

    def __init__(self, host: "Table"):
        self.host = host

    @property
    def left(self):
        return fhc.Div(fhc.Div("Material", cls="cell-header"), cls="left-row-header")

    @property
    def right(self):
        return fhc.Div(
            *(fhc.Div(_, cls="cell-header") for _ in self.host.COLUMN_ORDER),
            cls="right-row-header",
        )


class Footer:

    def __init__(self, host: "Table"):
        self.host = host

    @property
    def add_material_button(self):
        return fhc.Button(
            "New Material",
            cls="control-button",
            hx_get="/add",
            hx_target="main",
        )

    @property
    def left(self):
        return fhc.Div(self.add_material_button, cls="left-row-footer")

    @property
    def right(self):
        return fhc.Div(cls="right-row-footer")


class Data:
    def __init__(self, host: "Table"):
        self.host = host

    def delete_button(self, material: Material):
        return fhc.Div(
            fhc.Button(
                "Delete",
                cls="control-button",
                hx_post=f"/delete/{material.id}",
                hx_target="main",
            ),
            cls="cell-control",
        )

    def edit_button(self, material: Material):
        return fhc.Div(
            fhc.Button("Edit", cls="control-button"),
            cls="cell-control",
            hx_get=f"/edit/{material.id}",
            hx_target="main",
        )

    def create_row_left(self, material: Material):
        return fhc.Div(
            self.delete_button(material),
            self.edit_button(material),
            fhc.Div(material.name, cls="cell-data"),
            cls="left-row",
        )

    def create_row_right(self, material: Material):
        row_values = (
            fhc.Div(material.attribute_by_alias(col_name), cls="cell-data")
            for col_name in self.host.COLUMN_ORDER
        )
        return fhc.Div(*row_values, cls="right-row")

    @property
    def left(self):
        return fhc.Div(
            *[self.create_row_left(m) for m in self.host.materials], cls="left-data"
        )

    @property
    def right(self):
        return fhc.Div(
            *[self.create_row_right(m) for m in self.host.materials], cls="right-data"
        )


class Filter:

    def __init__(self, host: "Table"):
        self.host = host

    @property
    def filters(self) -> list[AttributeFilter]:
        # Return the selected value from the right dropdown
        return [AttributeFilter("Category", self.right.value)]

    @property
    def left(self):
        return fhc.Div(cls="filter-left")

    @property
    def right(self):
        return fhc.Form(
            hx_post="/filter",
            hx_trigger="change from:#category-filter, keyup delay:500ms from:#html",
            hx_target="#main",
        )(
            fhc.Select(
                fhc.Option("-", value="-"),
                *[fhc.Option(c, value=c) for c in self.host.categories],
                cls="filter-dropdown",
                id="category-filter",
            )
        )
        # return fhc.Div(dropdown, cls="filter-right")


class Table:
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

    def __init__(self, materials: list[Material]) -> None:
        self._materials = materials
        self.header = Header(self)
        self.filter = Filter(self)
        self.data = Data(self)
        self.footer = Footer(self)

    def apply_filters_to_materials(
        self, filters: list[AttributeFilter]
    ) -> list[Material]:
        return self._materials

    @property
    def materials(self):
        return self.apply_filters_to_materials(self.filter.filters)

    @property
    def categories(self) -> list[str]:
        return sorted(set(m.category for m in self._materials))

    @property
    def left_column(self):
        return fhc.Div(
            self.header.left,
            self.filter.left,
            self.data.left,
            self.footer.left,
            cls="column left-column",
        )

    @property
    def right_column(self):
        return fhc.Div(
            self.header.right,
            self.filter.right,
            self.data.right,
            self.footer.right,
            cls="column right-column",
        )

    def __ft__(self):
        """fastHTML render function."""
        return fhc.Div(
            self.left_column,
            self.right_column,
            cls="table",
        )
