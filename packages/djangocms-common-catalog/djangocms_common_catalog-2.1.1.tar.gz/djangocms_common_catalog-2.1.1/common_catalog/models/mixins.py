from django.utils.html import format_html_join
from django.utils.text import slugify


class AttrsMixin:
    """Slug and attributes mixin."""

    classes: list[str] = []
    name: str
    attributes: dict[str, dict[str, str]]

    @property
    def slug(self) -> str:
        """Get the code or the name as a slug."""
        return self.slugify_name()

    def get_attrs(self) -> dict[str, str]:
        """Get attibutes."""
        params: dict[str, str] = self.attributes.get("attributes", {}).copy() if self.attributes is not None else {}
        classes = (" ".join(self.classes + [self.slug, params.get("class", "")])).strip()
        if classes:
            params["class"] = classes
        return params

    @property
    def tag_attrs(self) -> str:
        """Html tag attributes."""
        return format_html_join(" ", '{}="{}"', [item for item in self.get_attrs().items()])

    def slugify_name(self) -> str:
        """Slugify name."""
        return slugify(self.name)
