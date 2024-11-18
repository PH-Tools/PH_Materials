import os
import fasthtml.common as fhc
from starlette.responses import RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/materials_db"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Material(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    conductivity = Column(String)


Base.metadata.create_all(bind=engine)

# FastHTML app setup
app, rt = fhc.fast_app()


@rt("/")
def get():
    session = SessionLocal()
    materials = session.query(Material).all()
    session.close()
    return fhc.Titled(
        "Materials List",
        fhc.Div(
            *[
                fhc.Div(
                    fhc.P(f"[ID-{m.id}] Name={m.name}, Conductivity={m.conductivity}")
                )
                for m in materials
            ]
        ),
        fhc.Form(
            fhc.Input(name="name", placeholder="Name"),
            fhc.Input(name="conductivity", placeholder="Conductivity"),
            fhc.Button("Add Material", type="submit"),
            method="post",
            action="/add",
        ),
    )


@rt("/add", methods=["POST"])
async def add(req: fhc.Request):
    form_data = await req.form()

    session = SessionLocal()
    new_material = Material(
        name=form_data.get("name"),
        conductivity=form_data.get("conductivity"),
    )
    session.add(new_material)
    session.commit()
    session.close()
    return RedirectResponse("/", status_code=303)


@rt("/delete/{material_id}", methods=["POST"])
def delete(material_id: int):
    session = SessionLocal()
    material = session.query(Material).filter(Material.id == material_id).first()
    if material:
        session.delete(material)
        session.commit()
    session.close()
    return RedirectResponse("/", status_code=303)


fhc.serve()
