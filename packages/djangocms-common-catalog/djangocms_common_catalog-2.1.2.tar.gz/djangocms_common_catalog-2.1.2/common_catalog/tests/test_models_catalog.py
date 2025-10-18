from django.test import SimpleTestCase, TestCase, override_settings

from common_catalog.models import Attribute, AttributeType, CatalogItem, Config, Location
from common_catalog.models.catalog import get_locations


class ConfigTest(TestCase):

    def test_str(self):
        conf = Config(namespace="The test")
        self.assertEqual(str(conf), "The test")


class GetLocationsTest(SimpleTestCase):

    def test_default(self):
        self.assertEqual(get_locations(), (
            ('above_title', 'Above the title'),
            ('under_title', 'Under the title'),
        ))

    @override_settings(COMMON_CATALOG_LOCATIONS=(('one', 'One'), ('two', 'Two')))
    def test_custom_locations(self):
        self.assertEqual(get_locations(), (
            ('one', 'One'),
            ('two', 'Two'),
        ))


class LocationTest(TestCase):

    def setUp(self):
        self.config = Config.objects.create(namespace="test")

    def test_empty_str(self):
        location = Location.objects.create(app_config=self.config)
        self.assertEqual(str(location), "")

    def test_str(self):
        location = Location.objects.create(app_config=self.config, code="above_title")
        self.assertEqual(str(location), "Above the title")


class AttributeTypeTest(TestCase):

    def test_str(self):
        attr = AttributeType.objects.create(name="The Test")
        self.assertEqual(str(attr), "The Test")


class AttributeTest(TestCase):

    def setUp(self):
        self.attribute_type = AttributeType.objects.create(name="The Test")

    def test_str(self):
        attr = Attribute.objects.create(attr_type=self.attribute_type, name="Item")
        self.assertEqual(str(attr), "The Test – Item")

    def test_slugify_name(self):
        attr = Attribute.objects.create(attr_type=self.attribute_type, name="Šílená kočička!")
        self.assertEqual(attr.slugify_name(), "the-test-silena-kocicka")


class CatalogItemTest(TestCase):

    def test_str(self):
        item = CatalogItem.objects.create(name="The Item")
        self.assertEqual(str(item), "The Item")
