from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import Config


@apphook_pool.register
class CommonCatalogApphook(CMSApp):

    app_name = "common_catalog"
    name = _("Common catalog")
    app_config = Config

    def get_urls(self, page=None, language=None, **kwargs):
        return ["common_catalog.urls"]

    def get_configs(self):
        return self.app_config.objects.all()

    def get_config(self, namespace):
        try:
            return self.app_config.objects.get(namespace=namespace)
        except self.app_config.DoesNotExist:
            return None

    def get_config_add_url(self):
        try:
            return reverse("admin:{}_{}_add".format(self.app_config._meta.app_label, self.app_config._meta.model_name))
        except AttributeError:
            return reverse("admin:{}_{}_add".format(self.app_config._meta.app_label, self.app_config._meta.module_name))
