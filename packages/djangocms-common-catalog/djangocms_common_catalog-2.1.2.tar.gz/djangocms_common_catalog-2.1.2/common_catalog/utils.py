from typing import Any

from django.conf import settings
from django.db.models import Q, QuerySet
from django.http import HttpRequest
from django.utils import timezone

ParamsDict = dict[str, Any]


def get_param_name() -> str:
    """Get parameter name for selected filter in url query."""
    return getattr(settings, "COMMON_CATALOG_FILTER_QUERY_NAME", "cocaf")


def get_page_list_params(request: HttpRequest) -> ParamsDict:
    """Get Books list page parameters."""
    params: ParamsDict = {}
    key = get_param_name()
    try:
        values = set(map(int, request.GET.getlist(key)))
        if values:
            params[key] = values
    except ValueError:
        pass
    return params


def get_filters_pk(request: HttpRequest) -> list[int]:
    """Get filters primary keys."""
    params = get_page_list_params(request)
    return params.get(get_param_name(), [])


def where_display() -> Q:
    """Get where part for queryset."""
    now = timezone.now()
    return Q(display_from__lte=now) & Q(display_until__gt=now) | Q(display_until__isnull=True)


def get_filtered_items_queryset(request: HttpRequest, queryset: QuerySet) -> QuerySet:
    """Get filter counter."""
    for filter_id in get_filters_pk(request):
        queryset &= queryset.filter(attrs__pk=filter_id)
    if hasattr(request, "current_app"):  # current_app is set in AppHookConfigMixin.dispatch.
        queryset &= queryset.filter(app_config__namespace=request.current_app)
    return queryset.filter(where_display())
