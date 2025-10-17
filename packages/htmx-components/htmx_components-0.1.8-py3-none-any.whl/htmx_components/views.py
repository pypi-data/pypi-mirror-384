"""Views for HTMX components."""

from enum import Enum
from typing import Any

from django import forms
from django.http import HttpResponse
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from django_htmx.http import HttpResponseClientRedirect, trigger_client_event


class ModalSize(Enum):
    SMALL = "sm"
    MEDIUM = "md"
    LARGE = "lg"
    XLARGE = "xl"
    NONE = None


class Fullscreen(Enum):
    TRUE = True
    SMALL = "sm"
    MEDIUM = "md"
    LARGE = "lg"
    XLARGE = "xl"
    XXLARGE = "xxl"
    NONE = None
    FALSE = False

    @property
    def modal_class(self) -> str | None:
        if self == Fullscreen.TRUE:
            return "modal-fullscreen"
        if self not in (Fullscreen.NONE, Fullscreen.FALSE):
            return f"modal-fullscreen-{self.value}-down"
        return None


class Modal:
    size: ModalSize = ModalSize.LARGE
    title: str | None = _("Form")  # type: ignore
    element_id: str = "modal"
    fullscreen: Fullscreen = Fullscreen.SMALL
    scrollable: bool | None = None
    centered: bool | None = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.__annotations__ and value is not None:
                annotation = self.__annotations__[key]
                enum_type = (
                    annotation
                    if isinstance(annotation, type) and issubclass(annotation, Enum)
                    else None
                )
                if enum_type and isinstance(value, str):
                    try:
                        value = enum_type(value)
                    except ValueError:
                        valid_values = [e.value for e in enum_type]
                        raise ValueError(
                            f"Invalid value for {key}: {value}. Must be one of {valid_values}"
                        )
            setattr(self, key, value)

    @property
    def dialog_classes(self) -> list[str]:
        attrs = ["scrollable", "centered"]
        classes = []
        for attr in attrs:
            if getattr(self, attr) is not None:
                attrs.append(f"modal-{attr}")
        if self.fullscreen.modal_class:
            classes.append(self.fullscreen.modal_class)
        if self.size is not None:
            classes.append(f"modal-{self.size.value}")
        return classes


class ModalFormView(FormView):
    form_class: type[forms.Form]
    modal: Modal = Modal()
    success_url: str | None = None  # Redirects client if set
    template_name = "htmx_components/form.html"

    def form_valid(self, form):
        if hasattr(form, "save"):
            form.save()
        if self.success_url:
            response = HttpResponseClientRedirect(self.success_url)
            return trigger_client_event(response, "modal:hide", after="swap")
        response = self.form_invalid(form)
        return response

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "modal": self.modal,
        }

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle GET requests and trigger modal show."""
        response = super().get(request, *args, **kwargs)
        return trigger_client_event(response, "modal:show", after="swap")
