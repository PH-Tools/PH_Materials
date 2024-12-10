from django import template

register = template.Library()


@register.filter
def display_conductivity(conductivity, request):
    unit_system = request.session.get("unit_system", "SI")
    if unit_system == "IP":
        conductivity = conductivity * 0.577789236
    return conductivity


@register.filter
def display_resistivity(conductivity, request):
    unit_system = request.session.get("unit_system", "SI")
    if unit_system == "IP":
        conductivity = 1 / (conductivity * 0.577789236 * 12)
    return conductivity


@register.filter
def display_conductivity_unit(material, request):
    unit_system = request.session.get("unit_system", "SI")
    if unit_system == "IP":
        return "Btu/(hr-ft-°F)"
    return "W/(m-K)"


@register.filter
def display_resistivity_unit(material, request):
    unit_system = request.session.get("unit_system", "SI")
    if unit_system == "IP":
        return "(hr-ft-°F)/Btu-in"
    return "(m-K)/W"
