from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from djangocms_text.fields import HTMLField
from parler.models import TranslatableModel, TranslatedFields

from ..constants import LOCATION_CHOICES
from .mixins import AttrsMixin


class Config(models.Model):

    namespace = models.CharField(_("Instance namespace"), default=None, max_length=50, unique=True)
    paginate_by = models.PositiveIntegerField(_("Paginate size"), default=50)
    template_prefix = models.SlugField(
        _("Template prefix"), null=True, blank=True,
        help_text="Used in settings.COMMON_CATALOG_DETAIL_PARENT_TEMPLATE = "
                  "'site_common_catalog/{}detail.html'.format(template_prefix)")

    class Meta:
        verbose_name = _('Configuration')
        verbose_name_plural = _('Configurations')

    def __str__(self):
        return self.namespace


def get_locations() -> tuple[tuple[str, str], ...]:
    """Get locations."""
    return settings.COMMON_CATALOG_LOCATIONS if hasattr(settings, "COMMON_CATALOG_LOCATIONS") else LOCATION_CHOICES


class Location(models.Model):
    """Location to display the filter type."""

    code = models.CharField(max_length=30, choices=get_locations(),
                            help_text=_("Code for position. Can be redefined in Django settings."))
    app_config = models.ForeignKey(
        Config,
        default=1,
        verbose_name=_("Configuration"),
        on_delete=models.CASCADE)

    class Meta:
        ordering = ["code"]
        verbose_name = _('Location')
        verbose_name_plural = _('Locations')

    def __str__(self):
        for code, label in get_locations():
            if code == self.code:
                return str(label)
        return self.code


class AttributeType(AttrsMixin, TranslatableModel):
    """Attribute type."""

    classes = ['filter-type']

    translations = TranslatedFields(
        name=models.CharField(_("Name"), unique=True, max_length=255),
    )
    attributes = models.JSONField(
        null=True, blank=True, encoder=DjangoJSONEncoder,
        help_text='HTML attributes as JSON data. E.g. {"data-name": "value", "id": 42}')
    display_in_location = models.ManyToManyField(
        Location,
        verbose_name=_("Display in location"),
        help_text=_("Display this filters type in the location."))
    position = models.SmallIntegerField(
        _("Position"), null=True, blank=True, help_text=_("Position in the attribute list."))

    class Meta:
        verbose_name = _('Attribute type')
        verbose_name_plural = _('Attribute types')

    def __str__(self):
        return self.name


class Attribute(AttrsMixin, TranslatableModel):
    """Items attribute."""

    classes = ['filter']

    attr_type = models.ForeignKey(AttributeType, verbose_name=_("Attribute type"), on_delete=models.CASCADE)
    translations = TranslatedFields(
        name=models.CharField(_("Name"), max_length=255),
    )
    position = models.SmallIntegerField(
        _("Position"), null=True, blank=True, help_text=_("Position in the attribute list."))
    attributes = models.JSONField(
        null=True, blank=True, encoder=DjangoJSONEncoder,
        help_text='HTML attributes as JSON data. E.g. {"data-name": "value", "id": 42}')

    class Meta:
        verbose_name = _('Attribute')
        verbose_name_plural = _('Attributes')

    def __str__(self):
        return f"{self.attr_type.name} – {self.name}"

    def slugify_name(self) -> str:
        """Slugify type and name."""
        return slugify(f"{self.attr_type.name} {self.name}")


class CatalogItem(AttrsMixin, TranslatableModel):
    """Catalog item."""

    classes = ['catalog-item']

    translations = TranslatedFields(
        name=models.CharField(_("Name"), max_length=255),
        ident=models.SlugField(_("Slug"), max_length=255, null=True, blank=True,
                               help_text=_('The part of the title that is used in the URL')),
        perex=HTMLField(_("Perex"), default=""),
        description=HTMLField(_("Description"), default=""),
    )
    attrs = models.ManyToManyField(Attribute, verbose_name=_("Attributes"), blank=True)
    display_from = models.DateTimeField(_("Display from"), default=timezone.now)
    display_until = models.DateTimeField(_("Display until"), blank=True, null=True)
    attributes = models.JSONField(
        null=True, blank=True, encoder=DjangoJSONEncoder,
        help_text='HTML attributes as JSON data. E.g. {"data-name": "value", "id": 42}')
    app_config = models.ForeignKey(
        Config,
        default=1,
        verbose_name=_("Configuration"),
        on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Catalog Item')
        verbose_name_plural = _('Catalog Items')
        ordering = ["-display_from"]

    def __str__(self):
        return self.name
