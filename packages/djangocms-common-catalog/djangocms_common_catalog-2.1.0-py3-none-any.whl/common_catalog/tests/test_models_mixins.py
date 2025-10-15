from django.test import SimpleTestCase

from common_catalog.models.mixins import AttrsMixin


class Attrs(AttrsMixin):
    classes: list[str] = []
    name: str = ""
    attributes: dict[str, dict[str, str]] = {}


class AttrsMixinTest(SimpleTestCase):

    def test_empty(self):
        attrs = Attrs()
        self.assertEqual(attrs.slug, "")
        self.assertEqual(attrs.slugify_name(), "")
        self.assertEqual(attrs.tag_attrs, "")

    def test(self):
        attrs = Attrs()
        attrs.classes = ["one", "two"]
        attrs.name = "Šílená kočička!"
        attrs.attributes = {
            "attributes": {
                "id": "42",
                "class": "dogs and cats",
                "data-name": "Name",
            }
        }
        self.assertEqual(attrs.slug, "silena-kocicka")
        self.assertEqual(attrs.slugify_name(), "silena-kocicka")
        self.assertEqual(attrs.tag_attrs, 'id="42" class="one two silena-kocicka dogs and cats" data-name="Name"')
