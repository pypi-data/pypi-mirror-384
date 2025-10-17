import uuid
from datetime import timedelta
from typing import TYPE_CHECKING, Union

from django.http import HttpRequest, HttpResponse
from django.urls import resolve

from territories_dashboard_lib.tracking_lib.enums import TRACKING_COOKIE_NAME, EventType
from territories_dashboard_lib.tracking_lib.geolocalisation.logic import (
    get_client_ip,
    get_country_from_geolite,
)
from territories_dashboard_lib.tracking_lib.models import CookieInfo, Event, Page

if TYPE_CHECKING:
    from territories_dashboard_lib.indicators_lib.models import Indicator, Theme


def get_or_set_tracking_cookie(request: HttpRequest, response: HttpResponse) -> str:
    tracking_cookie = request.COOKIES.get(TRACKING_COOKIE_NAME)
    if tracking_cookie is None:
        tracking_cookie = str(uuid.uuid4())
        response.set_cookie(
            key=TRACKING_COOKIE_NAME,
            value=tracking_cookie,
            max_age=timedelta(days=365),
        )
    try:
        CookieInfo.objects.get(id=tracking_cookie)
    except CookieInfo.DoesNotExist:
        ip_address = get_client_ip(request)
        country = get_country_from_geolite(ip_address)
        CookieInfo.objects.create(
            id=tracking_cookie, country=country, ip_address=ip_address
        )
    return tracking_cookie


def track_page(
    *,
    request: HttpRequest,
    response: HttpResponse,
    params=None,
    indicator: Union["Indicator", None] = None,
    theme: Union["Theme", None] = None,
):
    if params is None:
        params = {}
    try:
        cookie = get_or_set_tracking_cookie(request, response)
        match = resolve(request.path)
        view_name = match.view_name
        Page.objects.create(
            cookie=cookie,
            territory_id=params.get("territory_id"),
            territory_mesh=params.get("territory_mesh"),
            submesh=params.get("mesh"),
            cmp_territory_id=params.get("cmp_territory_id"),
            cmp_territory_mesh=params.get("cmp_territory_mesh"),
            indicator=indicator.id if indicator else None,
            indicator_name=indicator.name if indicator else None,
            theme=theme.id if theme else None,
            theme_name=theme.name if theme else None,
            url=request.get_full_path(),
            view=view_name,
        )
    except Exception as e:
        print("error while tracking indicator view")
        print(e)
    return response


def track_event(
    *, request: HttpRequest, response: HttpResponse, event_name=EventType, data
):
    try:
        cookie = get_or_set_tracking_cookie(request, response)
        match = resolve(request.path)
        view_name = match.view_name
        Event.objects.create(
            cookie=cookie,
            name=event_name,
            data=data,
            url=request.get_full_path(),
            view=view_name,
        )
    except Exception as e:
        print("error while tracking event")
        print(e)
    return response
