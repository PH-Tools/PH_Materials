"""Main module to run the Table Viewer."""

import fasthtml.common as fhc

from src.schemas.base import Base, engine
from src.routes.table import register_routes


# -- FastHTML app setup
app, rt = fhc.fast_app(
    hdrs=(
        fhc.Link(rel="stylesheet", href="src/static/table.css", type="text/css"),
        fhc.Link(
            rel="stylesheet", href="src/static/edit_material.css", type="text/css"
        ),
        fhc.Link(rel="script", href="src/static/scripts.js", type="text/javascript"),
    ),
)

# -- Create the Database and tables
Base.metadata.create_all(bind=engine)

# -- For Testing:
# remove_all_materials()

# -- Register routes
register_routes(rt)

# -- Run the App
fhc.serve()
