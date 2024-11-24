"""View: Table used to display a Menu Bar with Buttons at the top."""

import fasthtml.common as fhc


# TODO: Clean up the button styling
class Menu:

    def __init__(self) -> None:
        pass

    def __ft__(self):
        return fhc.Div(
            fhc.Button(
                "Load Materials from CSV",
                onclick="document.getElementById('file-input').click()",
            ),
            fhc.Input(
                type="file",
                id="file-input",
                style="display:none",
                onchange="uploadFile(event)",
            ),
            fhc.A(
                "Save Materials to CSV",
                href="/save_to_csv",
                download="materials.csv",
                cls="button",
            ),
            fhc.Script(src="/src/static/scripts.js"),
        )
