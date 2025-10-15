from typing import Any, TypedDict

from cms.models.pluginmodel import CMSPlugin
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.plugin_rendering import PluginContext
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html_join
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .models import (Attribute, CatalogFilter, CatalogFilteredItemsList, CatalogFilteredItemsNumber, CatalogFilterType,
                     CatalogItem)
from .utils import get_filtered_items_queryset, get_filters_pk, get_page_list_params


class FilterTypeDict(TypedDict):
    attrs: dict[str, Any]
    label: str
    count: int


def get_filter_data(request:  HttpRequest, items_queryset: QuerySet, instance: Attribute) -> FilterTypeDict:
    """Get filter data."""
    filters_count = items_queryset.filter(attrs__pk=instance.pk).count()
    params: dict[str, str] = {}
    classes = instance.classes.copy()
    classes.append("catalog-filter-plugin")
    if instance.pk in get_filters_pk(request):
        classes.append("selected")
        if not filters_count:
            classes.append("no-items")
    else:
        if not filters_count:
            classes.append("disabled")
    params["class"] = (" ".join(classes + [slugify(str(instance)), params.get("class", "")])).strip()
    params["data-filter_id"] = instance.pk
    filter_attrs = format_html_join(" ", '{}="{}"', [item for item in params.items()])
    return FilterTypeDict(attrs=filter_attrs, label=instance.name, count=filters_count)


@plugin_pool.register_plugin
class FilterPlugin(CMSPluginBase):

    model = CatalogFilter
    module = _('Common Catalog')
    name = _("Filter Plugin")
    render_template = "common_catalog/plugins/filter.html"
    allow_children = False
    cache = False

    def render(self, context: PluginContext, instance: CMSPlugin, placeholder: str) -> dict[str, Any]:
        context = super().render(context, instance, placeholder)  # type: ignore[misc]
        request = context['request']
        items_queryset = get_filtered_items_queryset(request, CatalogItem.objects.all())
        context["filter_data"] = get_filter_data(request, items_queryset, instance.attribute)
        return context


@plugin_pool.register_plugin
class FilterTypePlugin(CMSPluginBase):

    model = CatalogFilterType
    module = _('Common Catalog')
    name = _("Filter type Plugin")
    render_template = "common_catalog/plugins/filter_type.html"
    allow_children = False
    cache = False

    def render(self, context: PluginContext, instance: CMSPlugin, placeholder: str) -> dict[str, Any]:
        context = super().render(context, instance, placeholder)  # type: ignore[misc]
        request = context['request']
        items_queryset = get_filtered_items_queryset(request, CatalogItem.objects.all())
        context["form_type_items"] = [
            get_filter_data(request, items_queryset, filter_instance)
            for filter_instance in instance.attribute_type.attribute_set.translated(request.LANGUAGE_CODE).order_by(
                'translations__name')]
        return context


@plugin_pool.register_plugin
class FilteredItemsNumberPlugin(CMSPluginBase):

    model = CatalogFilteredItemsNumber
    module = _('Common Catalog')
    name = _("Filtered items number Plugin")
    render_template = "common_catalog/plugins/filtered_items_number.html"
    allow_children = False
    cache = False
    text_enabled = True

    def render(self, context: PluginContext, instance: CMSPlugin, placeholder: str) -> dict[str, Any]:
        context = super().render(context, instance, placeholder)  # type: ignore[misc]
        request = context['request']
        items_queryset = get_filtered_items_queryset(request, CatalogItem.objects.all())
        context["filtered_items_number"] = items_queryset.count()
        # HTML element attributes.
        params: dict[str, str] = {}
        if "title" not in params:
            params["title"] = _("The number of items according to the currently set filters.")
        classes = ["common-catalog", "filtered-items-number"]
        params["class"] = (" ".join(classes + [slugify(str(instance)), params.get("class", "")])).strip()
        context["plugin_attrs"] = format_html_join(" ", '{}="{}"', [item for item in params.items()])
        return context


@plugin_pool.register_plugin
class FilteredItemsListPlugin(CMSPluginBase):

    model = CatalogFilteredItemsList
    module = _('Common Catalog')
    name = _("Filtered items list Plugin")
    render_template = "common_catalog/plugins/filtered_items_list.html"
    allow_children = False
    cache = False

    def render(self, context: PluginContext, instance: CMSPlugin, placeholder: str) -> dict[str, Any]:
        context = super().render(context, instance, placeholder)  # type: ignore[misc]
        request = context['request']
        request.current_app = instance.app_config.namespace
        queryset = get_filtered_items_queryset(request, CatalogItem.objects.all())
        context["object_list"] = queryset[:instance.paginate_by]
        # HTML element attributes.
        params: dict[str, str] = {}
        classes = ["common-catalog", "plugin-list"]
        params["class"] = (" ".join(classes + [slugify(str(instance)), params.get("class", "")])).strip()
        context["plugin_attrs"] = format_html_join(" ", '{}="{}"', [item for item in params.items()])
        context["page_params"] = get_page_list_params(request)
        return context
