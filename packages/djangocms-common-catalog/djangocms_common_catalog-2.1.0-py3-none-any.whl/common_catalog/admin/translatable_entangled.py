from entangled.forms import EntangledFormMetaclass, EntangledModelForm
from parler.forms import TranslatableModelForm, TranslatableModelFormMetaclass

from ..models import AttributeType
from .fields import AttributesFormField


class CommonCatalogEntangledTranslatableMetaclass(EntangledFormMetaclass, TranslatableModelFormMetaclass):
    """Metaclass for admin form."""


class CommonCatalogEntangledTranslatableModelForm(
        EntangledModelForm, TranslatableModelForm, metaclass=CommonCatalogEntangledTranslatableMetaclass):
    """Model form with entangled and translatable fields."""

    class Meta:
        model = AttributeType
        fields: list[str] = []
        entangled_fields = {"attributes": ["attributes"]}

    attributes = AttributesFormField()

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data["attributes"]:
            del cleaned_data["attributes"]
        return cleaned_data
