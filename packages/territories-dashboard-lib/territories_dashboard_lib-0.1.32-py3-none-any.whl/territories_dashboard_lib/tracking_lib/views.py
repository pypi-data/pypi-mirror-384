import json
from datetime import timedelta

from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from pydantic import ValidationError

from territories_dashboard_lib.tracking_lib.logic import (
    track_event,
)
from territories_dashboard_lib.tracking_lib.models import Event
from territories_dashboard_lib.tracking_lib.payloads import EventPayload


@require_POST
@csrf_exempt
def track_event_view(request):
    try:
        data = json.loads(request.body)
        payload = EventPayload(**data)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except ValidationError as e:
        return JsonResponse({"error": e.errors()}, status=422)
    if (
        Event.objects.filter(created_at__gte=timezone.now() - timedelta(days=1)).count()
        > 1000
    ):
        return HttpResponse(status=429)
    response = HttpResponse()
    track_event(
        request=request,
        response=response,
        event_name=payload.event,
        data={
            "indicator": payload.indicator,
            "objet": payload.objet,
            "type": payload.type,
        },
    )
    return HttpResponse()
