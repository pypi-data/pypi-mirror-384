from django.utils.translation import gettext_lazy as _
from djangocms_attributes_field import fields


class AttributesFormField(fields.AttributesFormField):
    """Attributes Form Field."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label", _("Attributes"))
        kwargs.setdefault("required", False)
        kwargs.setdefault("widget", fields.AttributesWidget)
        self.excluded_keys = kwargs.pop("excluded_keys", [])
        super().__init__(*args, **kwargs)
