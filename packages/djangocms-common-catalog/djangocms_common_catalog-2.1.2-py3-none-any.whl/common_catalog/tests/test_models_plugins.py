from django.test import TestCase

from common_catalog.models import (Attribute, AttributeType, CatalogFilter, CatalogFilteredItemsList,
                                   CatalogFilteredItemsNumber, CatalogFilterType, Config)


class CatalogFilterTest(TestCase):

    def setUp(self):
        self.attribute_type = AttributeType.objects.create(name="The Test")
        self.attribute = Attribute.objects.create(attr_type=self.attribute_type, name="Item")

    def test_str(self):
        plugin = CatalogFilter.objects.create(attribute=self.attribute)
        self.assertEqual(str(plugin), "Item")


class CatalogFilterTypeTest(TestCase):

    def setUp(self):
        self.attribute_type = AttributeType.objects.create(name="The Test")

    def test_str(self):
        plugin = CatalogFilterType.objects.create(attribute_type=self.attribute_type)
        self.assertEqual(str(plugin), "The Test")


class CatalogFilteredItemsListTest(TestCase):

    def setUp(self):
        self.config = Config.objects.create(namespace="ns-test")

    def test_str(self):
        plugin = CatalogFilteredItemsList.objects.create(app_config=self.config)
        self.assertEqual(str(plugin), "ns-test")


class CatalogFilteredItemsNumberTest(TestCase):

    def setUp(self):
        self.config = Config.objects.create(namespace="ns-test")

    def test_str(self):
        plugin = CatalogFilteredItemsNumber.objects.create(app_config=self.config)
        self.assertEqual(str(plugin), "ns-test")
