from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html_join
from django.utils.translation import gettext_lazy as _
from parler.admin import TranslatableAdmin

from .forms import AttributeForm, AttributeTypeForm, CatalogItemForm
from .mixins import AllTranslationsMixin


class ConfigAdmin(admin.ModelAdmin):
    """Config Admin."""

    list_display = (
        'namespace',
        'paginate_by',
        'template_prefix',
    )


class AttributeTypeAdmin(AllTranslationsMixin, TranslatableAdmin):
    """Attribute Type admin."""

    form = AttributeTypeForm

    list_display = (
        'name',
        'position',
        'locations',
        'tag_attrs',
    )
    fieldsets = [
        (None, {
            "fields": ["name", "display_in_location", "position"]
        },),
        (_("Advanced options"), {
            "classes": ["collapse"],
            "fields": ["attributes"],
        },),
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Get queryset ordered by name."""
        return super().get_queryset(request).translated().order_by('translations__name')

    @admin.display(empty_value=_("Locations"))
    def locations(self, obj):
        return format_html_join("\n", '<div>{}</div>', [(str(location),) for location in obj.display_in_location.all()])


class AttributeAdmin(AllTranslationsMixin, TranslatableAdmin):
    """Attribute Admin."""

    form = AttributeForm
    fieldsets = [
        (None, {
            "fields": ["attr_type", "name", "position"]
        },),
        (_("Advanced options"), {
            "classes": ["collapse"],
            "fields": ["attributes"],
        },),
    ]

    list_display = (
        'name',
        'position',
        'attr_type',
        'attr_type__position',
        'tag_attrs',
    )
    list_filter = [
        'attr_type',
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Get queryset ordered by name."""
        return super().get_queryset(request).translated().order_by('translations__name')


class LocationAdmin(admin.ModelAdmin):
    """Location Admin."""

    list_display = (
        'code',
        'app_config',
    )
    list_filter = [
        'app_config',
    ]


class CatalogItemAdmin(AllTranslationsMixin, TranslatableAdmin):
    """Catalog Item Admin."""

    form = CatalogItemForm
    fieldsets = [
        (None, {
            "fields": [
                "name",
                "ident",
                "perex",
                "description",
                "attrs",
                "display_from",
                "display_until",
            ]
        },),
        (_("Advanced options"), {
            "classes": ["collapse"],
            "fields": ["app_config", "attributes"],
        },),
    ]

    list_display = (
        'name',
        'display_from',
        'display_until',
        'app_config',
        'tag_attrs',
    )
    list_filter = (
        'app_config',
        'display_from',
        'display_until',
    )
