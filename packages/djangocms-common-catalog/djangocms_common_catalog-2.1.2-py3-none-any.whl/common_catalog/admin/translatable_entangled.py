from django.utils.translation import gettext_lazy as _
from entangled.forms import EntangledFormMetaclass, EntangledModelForm
from parler.forms import TranslatableModelForm, TranslatableModelFormMetaclass

from ..models import AttributeType
from .fields import AttributesFormField


class CommonCatalogEntangledTranslatableMetaclass(EntangledFormMetaclass, TranslatableModelFormMetaclass):
    """Metaclass for admin form."""


class CommonCatalogEntangledTranslatableModelForm(
        EntangledModelForm, TranslatableModelForm, metaclass=CommonCatalogEntangledTranslatableMetaclass):
    """Model form with entangled and translatable fields."""

    extra_tag_attrs = AttributesFormField(label=_("Other HTML tag attributes"))

    class Meta:
        model = AttributeType
        entangled_fields = {"attributes": ["extra_tag_attrs"]}

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data["attributes"]:
            del cleaned_data["attributes"]
        return cleaned_data
