from cms.models.pluginmodel import CMSPlugin
from django.db import models
from django.utils.translation import gettext_lazy as _

from .catalog import Attribute, AttributeType, Config


class CatalogFilter(CMSPlugin):

    attribute = models.ForeignKey(Attribute, verbose_name=_("Attribute"), on_delete=models.CASCADE)

    def __str__(self):
        return str(self.attribute.name)


class CatalogFilterType(CMSPlugin):

    attribute_type = models.ForeignKey(AttributeType, verbose_name=_("Attribute type"), on_delete=models.CASCADE)

    def __str__(self):
        return str(self.attribute_type.name)


class CatalogFilteredItemsNumber(CMSPlugin):

    app_config = models.ForeignKey(
        Config,
        default=1,
        verbose_name=_("Configuration"),
        on_delete=models.CASCADE)

    def __str__(self):
        return str(self.app_config)


class CatalogFilteredItemsList(CMSPlugin):

    paginate_by = models.PositiveIntegerField(_("Paginate size"), default=10)
    app_config = models.ForeignKey(
        Config,
        default=1,
        verbose_name=_("Configuration"),
        on_delete=models.CASCADE)

    def __str__(self):
        return str(self.app_config)
