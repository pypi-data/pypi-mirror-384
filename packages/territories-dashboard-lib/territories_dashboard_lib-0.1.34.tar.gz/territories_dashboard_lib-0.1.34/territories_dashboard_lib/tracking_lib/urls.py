from django.urls import path

from territories_dashboard_lib.tracking_lib.views import track_event_view

app_name = "tracking-api"

urlpatterns = [
    path("event/", track_event_view, name="event"),
]
