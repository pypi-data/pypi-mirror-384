from django.urls import path

from .views import (
    geo_features_view,
    main_territory_view,
    precise_view,
    search_territories_view,
    territories_view,
)

app_name = "geo-api"

urlpatterns = [
    path(
        "geo-features/",
        geo_features_view,
        name="geo-features",
    ),
    path(
        "main-territory/",
        main_territory_view,
        name="main-territory",
    ),
    path("precise/", precise_view, name="precise"),
    path("territories/", territories_view, name="territories"),
    path("search-territories/", search_territories_view, name="search"),
]
