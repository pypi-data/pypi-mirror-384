from django.core.management.base import BaseCommand

from common_catalog.models import Attribute, AttributeType, CatalogItem


class Command(BaseCommand):
    help = "Upgrade attribute data."

    def make_upgrade(self, queryset):
        self.stdout.write(self.style.NOTICE("Upgrade model: %s, objects: %d." % (
            queryset.model.__name__, queryset.count())))
        saved = 0
        for item in queryset:
            if item.attributes is not None:
                if "attributes" in item.attributes:
                    item.attributes["extra_tag_attrs"] = item.attributes.pop("attributes")
                    item.save()
                    saved += 1
        self.stdout.write(self.style.SUCCESS("Saved %d items." % saved))

    def handle(self, *args, **options):
        self.make_upgrade(AttributeType.objects.all())
        self.make_upgrade(Attribute.objects.all())
        self.make_upgrade(CatalogItem.objects.all())
        self.stdout.write(self.style.SUCCESS("End of upgrade."))
