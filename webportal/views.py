from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django_htmx.http import retarget
from webportal.models import MaterialCategory, Material
from webportal.filters import MaterialCategoryFilter
from webportal.forms import MaterialForm
from webportal.resources import MaterialResource
from django.http import HttpResponse
from tablib import Dataset


def index(request):
    return render(request, "webportal/index.html")


@login_required
def materials_list(request):
    materials = Material.objects.all().select_related("category")
    materials_filter = MaterialCategoryFilter(request.GET, queryset=materials)
    paginator = Paginator(materials_filter.qs, settings.PAGE_SIZE)
    material_page = paginator.page(1)

    context = {
        "materials": material_page,
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
        "message": f"Material deleted successfully!",
    }
    return render(request, "webportal/partials/material-success.html", context)


@login_required
def get_materials(request):
    page = request.GET.get("page", 1)
    material_filter = MaterialCategoryFilter(
        request.GET,
        queryset=Material.objects.all().select_related("category"),
    )
    paginator = Paginator(material_filter.qs, settings.PAGE_SIZE)
    context = {
        "materials": paginator.page(page),
    }
    return render(
        request,
        "webportal/partials/materials-list-container.html#material_list",
        context,
    )


@login_required
def export_csv(request):
    # -- If the request comes from HTMX, do a client-side redirect but
    # -- as a normal (non-HTMX / Ajax) request to allow file downloading.
    if request.htmx:
        return HttpResponse(headers={"HX-Redirect": request.get_full_path()})

    material_filter = MaterialCategoryFilter(
        request.GET,
        queryset=Material.objects.all().select_related("category"),
    )

    data = MaterialResource().export(material_filter.qs)
    response = HttpResponse(data.csv)
    response["Content-Disposition"] = "attachment; filename=ph_materials.csv"
    return response


@login_required
def import_materials(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        resource = MaterialResource()
        dataset = Dataset()
        dataset.load(file.read().decode("utf-8"), format="csv")
        result = resource.import_data(dataset, user=request.user, dry_run=True)

        for row in result:
            for error in row.errors:
                print(error)

        if not result.has_errors():
            resource.import_data(dataset, user=request.user, dry_run=False)
            context = {"message": f"{len(dataset)} materials imported successfully!"}
            return render(request, "webportal/partials/material-success.html", context)
        else:
            context = {"message": "Sorry, an error occurred during upload"}
        return render(request, "webportal/partials/material-success.html", context)
    return render(request, "webportal/partials/import-materials.html", context={})
