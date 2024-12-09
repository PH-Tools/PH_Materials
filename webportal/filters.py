import django_filters
from django import forms

from webportal.models import Material, MaterialCategory


class MaterialCategoryFilter(django_filters.FilterSet):

    category = django_filters.ModelMultipleChoiceFilter(
        queryset=MaterialCategory.objects.all(), widget=forms.CheckboxSelectMultiple()
    )

    class Meta:
        model = Material
        fields = ("category",)
