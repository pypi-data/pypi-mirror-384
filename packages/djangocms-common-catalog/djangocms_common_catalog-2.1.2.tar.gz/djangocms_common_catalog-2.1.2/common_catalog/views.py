from typing import Optional

from cms.apphook_pool import apphook_pool
from cms.utils import get_language_from_request
from cms.utils.page import get_page_template_from_request
from django.conf import settings
from django.db.models.query import QuerySet
from django.db.utils import DataError
from django.http import Http404, HttpRequest, HttpResponse
from django.urls import Resolver404, resolve
from django.utils.translation import override
from django.views.generic import DetailView, ListView

from .models import CatalogItem, Config
from .utils import get_filtered_items_queryset, get_page_list_params, get_param_name


def get_app_instance(request: HttpRequest) -> tuple[str, Optional[Config]]:
    """Get application instance."""
    namespace, config = "", None
    if getattr(request, "current_page", None) and request.current_page.application_urls:
        app = apphook_pool.get_apphook(request.current_page.application_urls)
        if app and app.app_config:
            try:
                config = None
                with override(get_language_from_request(request)):
                    if hasattr(request, "toolbar") and hasattr(request.toolbar, "request_path"):
                        path = request.toolbar.request_path  # If v4 endpoint take request_path from toolbar
                    else:
                        path = request.path_info
                    namespace = resolve(path).namespace
                    config = app.get_config(namespace)
            except Resolver404:
                pass
    return namespace, config


class AppHookConfigMixin:

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.namespace, self.config = get_app_instance(request)
        request.current_app = self.namespace
        return super().dispatch(request, *args, **kwargs)  # type: ignore[misc]


class TemplateNameMixin:

    custom_template_name: str

    def get_template_names(self):
        names = super().get_template_names()
        name = getattr(settings, self.custom_template_name, None)
        if name is not None:
            names.insert(0, name)
        return names


class CatalogListView(AppHookConfigMixin, TemplateNameMixin, ListView):
    """Catalog list view."""

    model = CatalogItem
    custom_template_name = "COMMON_CATALOG_TEMPLATE_LIST"

    def get_paginate_by(self, queryset: QuerySet) -> int:
        try:
            return self.config.paginate_by  # type: ignore[union-attr]
        except AttributeError:
            return 50

    def get_queryset(self) -> QuerySet:
        """Get QuerySet."""
        return get_filtered_items_queryset(self.request, super().get_queryset())

    def get_context_data(self, **kwargs):
        kwargs.update({
            'filter_query_name': get_param_name(),
            'page_params': get_page_list_params(self.request),
        })
        return super().get_context_data(**kwargs)


class CatalogItemView(TemplateNameMixin, DetailView):
    """Catalog item view."""

    model = CatalogItem
    custom_template_name = "COMMON_CATALOG_TEMPLATE_DETAIL"

    def get_queryset(self) -> QuerySet:
        """Get QuerySet."""
        return get_filtered_items_queryset(self.request, super().get_queryset())

    def get_context_data(self, **kwargs):
        kwargs['filter_query_name'] = get_param_name()
        if hasattr(settings, "COMMON_CATALOG_DETAIL_PARENT_TEMPLATE"):
            name = settings.COMMON_CATALOG_DETAIL_PARENT_TEMPLATE
            item = kwargs["object"]
            prefix = item.app_config.template_prefix if item.app_config.template_prefix else ""
            kwargs["catalog_item_detail_parent_template"] = name.format(prefix)
        else:
            # This is the same as {% extends CMS_TEMPLATE %} in template.
            kwargs["catalog_item_detail_parent_template"] = get_page_template_from_request(self.request)
        return super().get_context_data(**kwargs)


class CatalogItemByNameView(CatalogItemView):
    """Catalog item view by Item name."""

    slug_url_kwarg = 'name'

    def get_object(self, queryset=None) -> CatalogItem:
        if queryset is None:
            queryset = self.get_queryset()

        queryset = get_filtered_items_queryset(self.request, queryset)
        slug = self.kwargs.get(self.slug_url_kwarg)
        value = slug.rstrip("/")

        contains = queryset.filter(translations__name__icontains=value)
        obj = contains.first()
        if obj is None:
            regex = queryset.filter(translations__name__iregex=value)
            try:
                obj = regex.first()
            except DataError:
                pass

        if obj is None:
            raise Http404("CatalogItem not found.")
        return obj
