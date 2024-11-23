from src.model.material import Material


def test_Material_from_dict_with_ID():
    d = {
        "id": 50,
        "name": "...",
        "category": "None",
        "conductivity_w_mk": "1.0",
        "emissivity": "0.9",
        "density_kg_m3": "1.0",
        "spec_heat_cap_J_kgK": "1.0",
        "roughness": "Rough",
        "thermal_absorptance": "0.9",
        "solar_absorptance": "0.9",
        "visible_absorptance": "0.9",
        "color": "...",
        "source": "...",
        "notes": "...",
    }
    m = Material(**d)
    assert m.id == 50


def test_Material_from_dict_without_ID():
    d = {
        "name": "...",
        "category": "...",
        "conductivity_w_mk": "1.0",
        "emissivity": "0.9",
        "density_kg_m3": "1.0",
        "spec_heat_cap_J_kgK": "1.0",
        "roughness": "Rough",
        "thermal_absorptance": "0.9",
        "solar_absorptance": "0.9",
        "visible_absorptance": "0.9",
        "color": "...",
        "source": "...",
        "notes": "...",
    }
    m = Material(**d)
    assert m.id == None
