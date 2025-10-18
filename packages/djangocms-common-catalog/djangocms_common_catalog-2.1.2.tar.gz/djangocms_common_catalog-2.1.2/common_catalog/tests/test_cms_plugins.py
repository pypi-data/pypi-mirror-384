from datetime import datetime, timezone

from cms.api import add_plugin
from cms.models import Placeholder
from cms.plugin_rendering import ContentRenderer
from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from common_catalog.cms_plugins import (FilteredItemsListPlugin, FilteredItemsNumberPlugin, FilterPlugin,
                                        FilterTypePlugin, get_filter_data)
from common_catalog.models import Attribute, AttributeType, CatalogItem, Config, Location
from common_catalog.utils import get_param_name


class AttributesTypeMixin:

    @classmethod
    def setUpTestData(cls):
        cls.placeholder = Placeholder.objects.create(slot='test')
        cls.param_name = get_param_name()
        cls.attribute_type = AttributeType.objects.create(name="The Test")

    def _render_plugin(self, plugin, query=""):
        request = RequestFactory().get(f"/{query}")
        request.LANGUAGE_CODE = "en"
        renderer = ContentRenderer(request=request)
        return renderer.render_plugin(plugin, {"request": request})


class FilterPluginTest(AttributesTypeMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.attribute = Attribute.objects.create(attr_type=cls.attribute_type, name="Item")

    def test_no_filters(self):
        plugin = add_plugin(self.placeholder, FilterPlugin, 'en', attribute=self.attribute)
        html = self._render_plugin(plugin)
        self.assertHTMLEqual(html, f"""
            <span class="filter catalog-filter-plugin disabled the-test-item" data-filter_id="{plugin.pk}">
                Item <span title="The number of items according to the currently set filters.">(0)</span>
            </span>""")

    def test_filter(self):
        attribute2 = Attribute.objects.create(attr_type=self.attribute_type, name="Item 2")
        item1 = CatalogItem.objects.create(name="Item One")
        item2 = CatalogItem.objects.create(name="Item Two")
        item1.attrs.add(self.attribute)
        item2.attrs.add(attribute2)
        plugin = add_plugin(self.placeholder, FilterPlugin, 'en', attribute=self.attribute)
        html = self._render_plugin(plugin, f"?{self.param_name}={self.attribute.pk}")
        self.assertHTMLEqual(html, f"""
            <span class="filter catalog-filter-plugin selected the-test-item" data-filter_id="{self.attribute.pk}">
                Item <span title="The number of items according to the currently set filters.">(1)</span>
            </span>""")


class FilterTypePluginTest(AttributesTypeMixin, TestCase):

    def test_empty(self):
        plugin = add_plugin(self.placeholder, FilterTypePlugin, 'en', attribute_type=self.attribute_type)
        html = self._render_plugin(plugin)
        self.assertHTMLEqual(html, f"""
            <div class="common-catalog-filter-type-frame">
                <div data-bs-toggle="collapse" href="#common-catalog-filter-{plugin.pk}" aria-expanded="true"
                    class="label">The Test</div>
                <div class="collapse show" id="common-catalog-filter-{plugin.pk}">
                </div>
            </div>""")

    def test_filters(self):
        attr1 = Attribute.objects.create(attr_type=self.attribute_type, name="Gamma")
        attr2 = Attribute.objects.create(attr_type=self.attribute_type, name="Beta")
        attr3 = Attribute.objects.create(attr_type=self.attribute_type, name="Alpha")

        plugin = add_plugin(self.placeholder, FilterTypePlugin, 'en', attribute_type=self.attribute_type)
        html = self._render_plugin(plugin)
        self.assertHTMLEqual(html, f"""
            <div class="common-catalog-filter-type-frame">
                <div data-bs-toggle="collapse" href="#common-catalog-filter-{plugin.pk}" aria-expanded="true"
                    class="label">The Test</div>
                <div class="collapse show" id="common-catalog-filter-1">
                    <span class="filter catalog-filter-plugin disabled the-test-alpha" data-filter_id="{attr3.pk}">
                        Alpha <span title="The number of items according to the currently set filters.">(0)</span>
                    </span>
                    <span class="filter catalog-filter-plugin disabled the-test-beta" data-filter_id="{attr2.pk}">
                        Beta <span title="The number of items according to the currently set filters.">(0)</span>
                    </span>
                    <span class="filter catalog-filter-plugin disabled the-test-gamma" data-filter_id="{attr1.pk}">
                        Gamma <span title="The number of items according to the currently set filters.">(0)</span>
                    </span>
                </div>
            </div>""")

    def test_selected_filters(self):
        attr1 = Attribute.objects.create(attr_type=self.attribute_type, name="Gamma")
        attr2 = Attribute.objects.create(attr_type=self.attribute_type, name="Beta")
        attr3 = Attribute.objects.create(attr_type=self.attribute_type, name="Alpha")

        item1 = CatalogItem.objects.create(name="Item One")
        item2 = CatalogItem.objects.create(name="Item Two")
        item3 = CatalogItem.objects.create(name="Item Three")
        item4 = CatalogItem.objects.create(name="Item Four")

        item1.attrs.add(attr1)
        item1.attrs.add(attr2)
        item1.attrs.add(attr3)

        item2.attrs.add(attr2)
        item2.attrs.add(attr3)

        item3.attrs.add(attr1)
        item3.attrs.add(attr3)

        item4.attrs.add(attr1)
        item4.attrs.add(attr2)

        plugin = add_plugin(self.placeholder, FilterTypePlugin, 'en', attribute_type=self.attribute_type)
        params = f"?{self.param_name}={attr2.pk}&{self.param_name}={attr3.pk}"
        html = self._render_plugin(plugin, params)
        self.assertHTMLEqual(html, f"""
            <div class="common-catalog-filter-type-frame">
                <div data-bs-toggle="collapse" href="#common-catalog-filter-{plugin.pk}" aria-expanded="true"
                    class="label">The Test</div>
                <div class="collapse show" id="common-catalog-filter-{plugin.pk}">
                    <span class="filter catalog-filter-plugin selected the-test-alpha" data-filter_id="{attr3.pk}">
                        Alpha <span title="The number of items according to the currently set filters.">(2)</span>
                    </span>
                    <span class="filter catalog-filter-plugin selected the-test-beta" data-filter_id="{attr2.pk}">
                        Beta <span title="The number of items according to the currently set filters.">(2)</span>
                    </span>
                    <span class="filter catalog-filter-plugin the-test-gamma" data-filter_id="{attr1.pk}">
                        Gamma <span title="The number of items according to the currently set filters.">(1)</span>
                    </span>
                </div>
            </div>""")


class FilteredItemsNumberPluginTest(AttributesTypeMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.config = Config.objects.create(namespace="ns-test")

    def test_no_items(self):
        plugin = add_plugin(self.placeholder, FilteredItemsNumberPlugin, 'en', app_config=self.config)
        html = self._render_plugin(plugin)
        self.assertHTMLEqual(html, """
            <span title="The number of items according to the currently set filters."
                class="common-catalog filtered-items-number ns-test">0</span>""")

    def test_items(self):
        attr1 = Attribute.objects.create(attr_type=self.attribute_type, name="Gamma")
        attr2 = Attribute.objects.create(attr_type=self.attribute_type, name="Beta")
        attr3 = Attribute.objects.create(attr_type=self.attribute_type, name="Alpha")

        item1 = CatalogItem.objects.create(name="Item One")
        item2 = CatalogItem.objects.create(name="Item Two")
        item3 = CatalogItem.objects.create(name="Item Three")

        item1.attrs.add(attr1)
        item1.attrs.add(attr2)
        item1.attrs.add(attr3)

        item2.attrs.add(attr1)

        item3.attrs.add(attr2)
        item3.attrs.add(attr3)

        plugin = add_plugin(self.placeholder, FilteredItemsNumberPlugin, 'en', app_config=self.config)
        html = self._render_plugin(plugin, f"?{self.param_name}={attr2.pk}&{self.param_name}={attr2.pk}")
        self.assertHTMLEqual(html, """
            <span title="The number of items according to the currently set filters."
                class="common-catalog filtered-items-number ns-test">2</span>""")


@override_settings(ROOT_URLCONF='common_catalog.tests.urls')
class FilteredItemsListPluginTest(AttributesTypeMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.config = Config.objects.create(namespace="ns-test")

    def test_no_items(self):
        plugin = add_plugin(self.placeholder, FilteredItemsListPlugin, 'en', app_config=self.config)
        html = self._render_plugin(plugin)
        self.assertHTMLEqual(html, """<div class="common-catalog plugin-list ns-test"></div>""")

    def test_items(self):
        item1 = CatalogItem.objects.create(
            name="Item One", app_config=self.config, display_from=datetime(2024, 9, 2, tzinfo=timezone.utc))
        item2 = CatalogItem.objects.create(
            name="Item Two", app_config=self.config, display_from=datetime(2024, 9, 1, tzinfo=timezone.utc))
        CatalogItem.objects.create(name="Item Three", display_from=datetime(2024, 9, 3, tzinfo=timezone.utc))

        plugin = add_plugin(self.placeholder, FilteredItemsListPlugin, 'en', app_config=self.config)
        html = self._render_plugin(plugin)
        self.assertHTMLEqual(html, f"""
            <div class="common-catalog plugin-list ns-test">
                <a class="catalog-item item-one" href="/{item1.pk}/">
                    <ul class="filters above"></ul>
                    <h4 class="item-name">Item One</h4>
                    <ul class="grouped-filters bottom"></ul>
                </a>
                <a class="catalog-item item-two" href="/{item2.pk}/">
                    <ul class="filters above"></ul>
                    <h4 class="item-name">Item Two</h4>
                    <ul class="grouped-filters bottom"></ul>
                </a>
            </div>""")

    def test_items_with_attrs(self):
        location_top = Location.objects.create(app_config=self.config, code="above_title")
        location_bottom = Location.objects.create(app_config=self.config, code="under_title")

        attr_top = AttributeType.objects.create(name="Top")
        attr_bottom = AttributeType.objects.create(name="Bottom")
        attr_top.display_in_location.add(location_top)
        attr_bottom.display_in_location.add(location_bottom)

        attr1 = Attribute.objects.create(attr_type=attr_top, name="Gamma")
        attr2 = Attribute.objects.create(attr_type=attr_top, name="Beta")
        attr3 = Attribute.objects.create(attr_type=attr_top, name="Alpha")

        attr4 = Attribute.objects.create(attr_type=attr_bottom, name="Red")
        attr5 = Attribute.objects.create(attr_type=attr_bottom, name="Green")

        item1 = CatalogItem.objects.create(
            name="Item One", app_config=self.config, display_from=datetime(2024, 9, 2, tzinfo=timezone.utc))
        item2 = CatalogItem.objects.create(
            name="Item Two", app_config=self.config, display_from=datetime(2024, 9, 1, tzinfo=timezone.utc))
        item3 = CatalogItem.objects.create(name="Item Three", display_from=datetime(2024, 9, 3, tzinfo=timezone.utc))

        item1.attrs.add(attr1)
        item1.attrs.add(attr2)
        item1.attrs.add(attr3)
        item1.attrs.add(attr4)
        item1.attrs.add(attr5)

        item2.attrs.add(attr2)
        item2.attrs.add(attr4)

        item3.attrs.add(attr3)
        item3.attrs.add(attr5)

        plugin = add_plugin(self.placeholder, FilteredItemsListPlugin, 'en', app_config=self.config)
        html = self._render_plugin(plugin)
        self.assertHTMLEqual(html, f"""
            <div class="common-catalog plugin-list ns-test">
                <a class="catalog-item item-one" href="/{item1.pk}/">
                    <ul class="filters above">
                        <li class="filter top-gamma">Gamma</li>
                        <li class="filter top-beta">Beta</li>
                        <li class="filter top-alpha">Alpha</li>
                    </ul>
                    <h4 class="item-name">Item One</h4>
                    <ul class="grouped-filters bottom">
                        <li class="filter-type bottom">
                            <ul class="filters bottom">
                                <li class="filter bottom-red">Red</li>
                                <li class="filter bottom-green">Green</li>
                            </ul>
                        </li>
                    </ul>
                </a>
                <a class="catalog-item item-two" href="/{item2.pk}/">
                    <ul class="filters above">
                        <li class="filter top-beta">Beta</li>
                    </ul>
                    <h4 class="item-name">Item Two</h4>
                    <ul class="grouped-filters bottom">
                        <li class="filter-type bottom">
                            <ul class="filters bottom">
                                <li class="filter bottom-red">Red</li>
                            </ul>
                        </li>
                    </ul>
                </a>
            </div>""")


class GetFilterDataTest(AttributesTypeMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.attribute = Attribute.objects.create(attr_type=cls.attribute_type, name="Item")

    def test_empty(self):
        request = RequestFactory().get("/")
        queryset = CatalogItem.objects.all()
        data = get_filter_data(request, queryset, self.attribute)
        self.assertEqual(data, {
            'attrs': 'class="filter catalog-filter-plugin disabled the-test-item" '
                     f'data-filter_id="{self.attribute.pk}"',
            'label': 'Item',
            'count': 0
        })

    def test_items(self):
        item1 = CatalogItem.objects.create(name="Item One")
        item2 = CatalogItem.objects.create(name="Item Two")
        item1.attrs.add(self.attribute)
        item2.attrs.add(self.attribute)
        request = RequestFactory().get("/")
        queryset = CatalogItem.objects.all()
        data = get_filter_data(request, queryset, self.attribute)
        self.assertEqual(data, {
            'attrs': 'class="filter catalog-filter-plugin the-test-item" '
                     f'data-filter_id="{self.attribute.pk}"',
            'label': 'Item',
            'count': 2
        })

    def test_filtered_items(self):
        attribute = Attribute.objects.create(attr_type=self.attribute_type, name="Other")
        item1 = CatalogItem.objects.create(name="Item One")
        item2 = CatalogItem.objects.create(name="Item Two")
        item1.attrs.add(self.attribute)
        item2.attrs.add(attribute)
        request = RequestFactory().get(f"/?{self.param_name}={attribute.pk}")
        queryset = CatalogItem.objects.all()
        data = get_filter_data(request, queryset, self.attribute)
        self.assertEqual(data, {
            'attrs': 'class="filter catalog-filter-plugin the-test-item" '
                     f'data-filter_id="{self.attribute.pk}"',
            'label': 'Item',
            'count': 1
        })
