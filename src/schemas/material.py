from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Column, Integer, String, Float

from src.schemas.base import Base


class MaterialDB(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True, index=True)
    name = mapped_column(String, nullable=True, index=True)
    category = mapped_column(String, nullable=True)
    conductivity_w_mk = mapped_column(Float, nullable=True)
    emissivity = mapped_column(Float, nullable=True)
    density_kg_m3 = mapped_column(Float, nullable=True)
    spec_heat_cap_J_kgK = mapped_column(Float, nullable=True)
    roughness = mapped_column(String, nullable=True)
    thermal_absorptance = mapped_column(Float, nullable=True)
    solar_absorptance = mapped_column(Float, nullable=True)
    visible_absorptance = mapped_column(Float, nullable=True)
    color = mapped_column(String, nullable=True)
    source = mapped_column(String, nullable=True)
    notes = mapped_column(String, nullable=True)
