from pydantic import BaseModel


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
