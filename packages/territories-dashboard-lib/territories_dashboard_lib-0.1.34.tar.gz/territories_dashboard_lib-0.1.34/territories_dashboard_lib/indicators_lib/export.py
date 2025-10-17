import csv

from django.http import HttpRequest, HttpResponse

from territories_dashboard_lib.tracking_lib.enums import EventType, GraphType
from territories_dashboard_lib.tracking_lib.logic import track_event

from .models import Indicator


def export_to_csv(
    request: HttpRequest, indicator: Indicator, graph_name: GraphType, data: list[dict]
):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="{indicator.name}_{graph_name}.csv"'
    )
    writer = csv.writer(response)
    if data:
        writer.writerow(data[0].keys())
    for row in data:
        writer.writerow(row.values())
    response = track_event(
        request=request,
        response=response,
        event_name=EventType.download,
        data={"indicator": indicator.name, "objet": graph_name, "type": "csv"},
    )
    return response
