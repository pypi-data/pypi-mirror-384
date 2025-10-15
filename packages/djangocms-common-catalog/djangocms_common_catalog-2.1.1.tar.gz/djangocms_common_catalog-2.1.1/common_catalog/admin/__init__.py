from django.contrib import admin

from ..models import Attribute, AttributeType, CatalogItem, Config, Location
from .options import AttributeAdmin, AttributeTypeAdmin, CatalogItemAdmin, ConfigAdmin, LocationAdmin

admin.site.register(Config, ConfigAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(AttributeType, AttributeTypeAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(CatalogItem, CatalogItemAdmin)
