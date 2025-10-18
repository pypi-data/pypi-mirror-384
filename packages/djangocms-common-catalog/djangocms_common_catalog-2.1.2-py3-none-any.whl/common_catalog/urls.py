from django.urls import path

from .views import CatalogItemByNameView, CatalogItemView, CatalogListView

urlpatterns = [
    path("<int:pk>/", CatalogItemView.as_view(), name="item"),
    path("<path:name>", CatalogItemByNameView.as_view(), name="item_by_name"),
    path("", CatalogListView.as_view(), name="list"),
]
