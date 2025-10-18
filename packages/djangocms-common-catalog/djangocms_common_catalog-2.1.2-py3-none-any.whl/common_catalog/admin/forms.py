from django.db.models import F
from django.forms.models import ModelChoiceIterator, ModelChoiceIteratorValue, ModelMultipleChoiceField

from ..models import Attribute, AttributeType, CatalogItem
from .translatable_entangled import CommonCatalogEntangledTranslatableModelForm


class AttributeTypeForm(CommonCatalogEntangledTranslatableModelForm):
    """Attribute Type form."""

    class Meta(CommonCatalogEntangledTranslatableModelForm.Meta):
        model = AttributeType
        untangled_fields = [
            'name',
            'position',
            'display_in_location',
        ]


class AttributeForm(CommonCatalogEntangledTranslatableModelForm):
    """Attribute form."""

    class Meta(CommonCatalogEntangledTranslatableModelForm.Meta):
        model = Attribute
        untangled_fields = [
            'name',
            'position',
            'attr_type',
        ]


class AttrsIterator(ModelChoiceIterator):

    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        for group in AttributeType.objects.all().order_by(F("position").asc(nulls_last=True)):
            choices = []
            for obj in group.attribute_set.all().order_by(F("position").asc(nulls_last=True)):
                choices.append((ModelChoiceIteratorValue(self.field.prepare_value(obj), obj), obj.name))
            yield (self.field.label_from_instance(group), choices)


class AttrsField(ModelMultipleChoiceField):
    """Attrs Field."""

    iterator = AttrsIterator


class CatalogItemForm(CommonCatalogEntangledTranslatableModelForm):
    """Catalog Item form."""

    class Meta(CommonCatalogEntangledTranslatableModelForm.Meta):
        model = CatalogItem
        untangled_fields = [
            'name',
            'ident',
            'perex',
            'description',
            'attrs',
            'display_from',
            'display_until',
            'app_config',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        attrs = self.fields["attrs"]
        queryset = attrs.queryset.order_by(
            F("attr_type__position").asc(nulls_last=True), "attr_type", F("position").asc(nulls_last=True))
        self.fields["attrs"] = AttrsField(queryset=queryset, label=attrs.label, help_text=attrs.help_text)
