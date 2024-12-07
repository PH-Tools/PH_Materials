from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django_htmx.http import retarget
from webportal.models import MaterialCategory, Material
from webportal.filters import MaterialCategoryFilter
from webportal.forms import MaterialForm


def index(request):
    return render(request, "webportal/index.html")


@login_required
def materials_list(request):
    materials = Material.objects.all().select_related("category")
    materials_filter = MaterialCategoryFilter(request.GET, queryset=materials)

    context = {
        "filter": materials_filter,
    }
    if request.htmx:
        return render(
            request, "webportal/partials/materials-list-container.html", context
        )
    else:
        return render(request, "webportal/materials-list.html", context)


@login_required
def create_material(request):
    if request.method == "POST":
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save(commit=False)
            material.user = request.user
            material.save()
            context = {"message": "Material created successfully!"}
            return render(request, "webportal/partials/material-success.html", context)
        else:
            context = {"form": form}
            response = render(
                request, "webportal/partials/create-material.html", context
            )
            return retarget(response, "#materials-list-block")

    context = {"form": MaterialForm()}
    return render(request, "webportal/partials/create-material.html", context)


@login_required
def update_material(request, pk: int):
    material = get_object_or_404(Material, pk=pk)

    if request.method == "POST":
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            material = form.save()
            context = {"message": "Material updated successfully!"}
            return render(request, "webportal/partials/material-success.html", context)
        else:
            context = {"form": form, "material": material}
            response = render(
                request, "webportal/partials/update-material.html", context
            )
            return retarget(response, "#materials-list-block")

    context = {
        "form": MaterialForm(instance=material),
        "material": material,
    }

    return render(request, "webportal/partials/update-material.html", context)


@login_required
@require_http_methods(["DELETE"])
def delete_material(request, pk: int):
    material = get_object_or_404(Material, pk=pk)
    material.delete()
    context = {
        "message": f"Transaction deleted successfully!",
    }
    return render(request, "webportal/partials/material-success.html", context)
