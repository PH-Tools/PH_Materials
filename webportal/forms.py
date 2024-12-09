from django import forms

from webportal.models import Material, MaterialCategory


class MaterialForm(forms.ModelForm):

    def clean_name(self) -> str:
        name = self.cleaned_data["name"]
        if not name:
            raise forms.ValidationError("Please enter a valid name.")
        return name

    def clean_conductivity(self) -> str:
        conductivity = self.cleaned_data["conductivity"]
        if conductivity <= 0:
            raise forms.ValidationError("Conductivity must be greater than 0")
        return conductivity

    def clean_emissivity(self) -> str:
        emissivity = self.cleaned_data["emissivity"]
        if emissivity < 0 or emissivity > 1:
            raise forms.ValidationError("Emissivity must be between 0.0 and 1.0")
        return emissivity

    class Meta:
        model = Material
        fields = {
            "name",
            "conductivity",
            "emissivity",
            "category",
            "source",
            "comments",
            "color_argb",
        }
