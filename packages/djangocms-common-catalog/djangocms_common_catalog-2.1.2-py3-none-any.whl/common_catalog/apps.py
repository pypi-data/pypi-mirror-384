from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CommonCatalog(AppConfig):
    name = 'common_catalog'
    verbose_name = _('Common Catalog')
