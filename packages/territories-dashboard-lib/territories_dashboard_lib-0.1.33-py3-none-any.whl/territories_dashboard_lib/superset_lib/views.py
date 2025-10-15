from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

from territories_dashboard_lib.superset_lib.payloads import GuestTokenPayload

from .guest_token import get_guest_token
from .models import Dashboard


@require_GET
def guest_token_view(request):
    payload = GuestTokenPayload(**request.GET.dict())
    guest_token = get_guest_token(payload.dashboard)
    return HttpResponse(guest_token)


@require_GET
def dashboards_view(request):
    dashboards = Dashboard.objects.order_by("order", "label")
    data = [{"label": d.label, "superset_id": d.superset_id} for d in dashboards]
    return JsonResponse(data, safe=False)
