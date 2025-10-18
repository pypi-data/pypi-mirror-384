from django.urls import include, path

urlpatterns = [
    path('', include(('common_catalog.urls', 'common_catalog')))
]
