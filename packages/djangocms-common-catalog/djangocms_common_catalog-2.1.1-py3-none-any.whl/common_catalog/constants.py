from enum import Enum, unique

from django.utils.translation import gettext_lazy as _


@unique
class LocationType(Enum):
    above_title = "above_title"
    under_title = "under_title"


LOCATION_CHOICES = (
    (LocationType.above_title.value, _("Above the title")),
    (LocationType.under_title.value, _("Under the title")),
)
