from django.urls import path

from .views import dashboards_view, guest_token_view

app_name = "superset-api"

urlpatterns = [
    path("guest-token/", guest_token_view, name="guest-token"),
    path("dashboards/", dashboards_view, name="dashboards"),
]
