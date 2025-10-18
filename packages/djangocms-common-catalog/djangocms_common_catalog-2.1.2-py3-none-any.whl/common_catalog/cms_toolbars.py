from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.urlutils import admin_reverse
from django.utils.translation import gettext_lazy as _


class CommonCatalogToolbar(CMSToolbar):

    supported_apps = ['common_catalog']

    def populate(self):

        if not self.is_current_app:
            return

        if 'common_catalog' in self.request.resolver_match.app_names:
            label = " ".join(self.request.resolver_match.namespaces)
        else:
            label = _('Common Catalog')
        menu = self.toolbar.get_or_create_menu('common_catalog_cms_integration-common_catalog', label)

        menu.add_sideframe_item(
            name=_('Items list'),
            url=admin_reverse('common_catalog_catalogitem_changelist'),
        )

        menu.add_modal_item(
            name=_('Add a new item'),
            url=admin_reverse('common_catalog_catalogitem_add'),
        )

        buttonlist = self.toolbar.add_button_list()

        buttonlist.add_sideframe_button(
            name=_('Items list'),
            url=admin_reverse('common_catalog_catalogitem_changelist'),
        )

        buttonlist.add_modal_button(
            name=_('Add a new item'),
            url=admin_reverse('common_catalog_catalogitem_add'),
        )
        if self.request.resolver_match.url_name == 'item' and 'common_catalog' in self.request.resolver_match.app_names:
            object_id = self.request.resolver_match.kwargs.get("pk")
            if object_id:
                buttonlist.add_modal_button(
                    name=_('Edit item'),
                    url=admin_reverse('common_catalog_catalogitem_change', kwargs={"object_id": object_id}),
                )


toolbar_pool.register(CommonCatalogToolbar)
