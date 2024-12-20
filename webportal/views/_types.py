from enum import Enum

from django.core.handlers.wsgi import WSGIRequest

from webportal.forms import MaterialSearchForm
from webportal.models import Layer, User


def get_user(request: WSGIRequest) -> User:
    """Wrapper function to mask type-hint warnings."""
    return request.user  # type: ignore


class UnitSystem(Enum):
    SI = "SI"
    IP = "IP"


class LayerView:
    """A helper class to manage the Layer and its segments/forms in the Assembly view."""

    def __init__(self, layer: Layer):
        self.layer = layer
        self.segments = layer.get_ordered_segments()
        self.forms = [
            MaterialSearchForm(
                prefix=f"form_{segment.pk}",
                initial={"material": segment.material.pk if segment.material else None},
            )
            for segment in self.segments
        ]

    @property
    def segments_and_forms(self):
        return zip(self.segments, self.forms)
