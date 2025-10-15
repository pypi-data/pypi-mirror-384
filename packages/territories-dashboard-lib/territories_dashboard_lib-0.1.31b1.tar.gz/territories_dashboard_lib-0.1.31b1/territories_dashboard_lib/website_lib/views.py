from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.gzip import gzip_page

from territories_dashboard_lib.indicators_lib.models import Indicator, Theme
from territories_dashboard_lib.superset_lib.logic import make_filter
from territories_dashboard_lib.superset_lib.models import Dashboard
from territories_dashboard_lib.superset_lib.serializers import serialize_dashboard
from territories_dashboard_lib.tracking_lib.logic import track_page
from territories_dashboard_lib.website_lib.models import (
    GlossaryItem,
    LandingPage,
    StaticPage,
)
from territories_dashboard_lib.website_lib.params import with_params
from territories_dashboard_lib.website_lib.serializers import (
    serialize_indicator,
    serialize_sub_themes,
)


@gzip_page
def landing_page_view(request):
    landing_page = LandingPage.objects.first()
    response = render(
        request,
        "territories_dashboard_lib/website/pages/page.html",
        {"landing_page": landing_page},
    )
    response = track_page(request=request, response=response)
    return response


@gzip_page
def static_page_view(request, page_url):
    static_page = get_object_or_404(StaticPage, url=page_url)
    return render(
        request,
        "territories_dashboard_lib/website/pages/static/page.html",
        {"static_page": static_page},
    )


@gzip_page
def lexique_page_view(request):
    lexique = GlossaryItem.objects.all()
    context = {"lexique": lexique}
    response = render(
        request, "territories_dashboard_lib/website/pages/lexique/page.html", context
    )
    return response


def themes_redirect_view(request):
    first_theme = Theme.objects.order_by("ordering").first()
    target_url = reverse("website:theme", kwargs={"theme_name": first_theme.name})
    get_params = request.GET.urlencode()
    if get_params:
        target_url = f"{target_url}?{get_params}"
    return redirect(target_url)


@gzip_page
@with_params
def comparison_view(request, *, theme_name, context):
    theme = get_object_or_404(Theme, name=theme_name)
    sub_themes = serialize_sub_themes(theme)
    themes = Theme.objects.order_by("ordering")
    context["theme"] = theme
    context["themes"] = themes
    context["sub_themes"] = sub_themes
    response = render(
        request,
        "territories_dashboard_lib/website/pages/indicators/comparaison/[theme]/page.html",
        context,
    )
    response = track_page(
        request=request,
        response=response,
        params=context["params"],
        theme=theme,
    )
    return response


def comparison_redirect_view(request):
    first_theme = Theme.objects.order_by("ordering").first()
    target_url = reverse("website:comparison", kwargs={"theme_name": first_theme.name})
    get_params = request.GET.urlencode()
    if get_params:
        target_url = f"{target_url}?{get_params}"
    return redirect(target_url)


@gzip_page
@with_params
def theme_page_view(request, *, theme_name, context):
    theme = get_object_or_404(Theme, name=theme_name)
    sub_themes = serialize_sub_themes(theme)
    themes = Theme.objects.all().order_by("ordering")
    context["theme"] = theme
    context["themes"] = themes
    context["sub_themes"] = sub_themes
    response = render(
        request,
        "territories_dashboard_lib/website/pages/indicators/themes/page.html",
        context,
    )
    response = track_page(
        request=request,
        response=response,
        params=context["params"],
        theme=theme,
    )
    return response


def apply_filters(request, indicator):
    filters = []
    for dimension in indicator.dimensions.all():
        url_filters = request.GET.getlist(dimension.db_name)
        db_filters = [f for f in dimension.filters.all()]
        for f in db_filters:
            f.set_from_url = "!" + f.db_name in url_filters or f.db_name in url_filters
            f.current = (
                f.default
                and "!" + f.db_name not in url_filters
                or f.db_name in url_filters
            )
        filters.append([dimension, db_filters])
    return filters


@gzip_page
@with_params
def indicator_details_view(request, *, indicator_name, context):
    indicator = get_object_or_404(Indicator, name=indicator_name)
    theme = indicator.sub_theme.theme
    sub_themes = serialize_sub_themes(theme)
    themes = Theme.objects.all().order_by("ordering")
    filters = apply_filters(request, indicator)
    context["indicator"] = serialize_indicator(indicator)
    context["themes"] = themes
    context["theme"] = theme
    context["subtheme"] = indicator.sub_theme
    context["sub_themes"] = sub_themes
    context["filters"] = filters
    response = render(
        request,
        "territories_dashboard_lib/website/pages/indicators/details/page.html",
        context=context,
    )
    response = track_page(
        request=request,
        response=response,
        params=context["params"],
        indicator=indicator,
        theme=theme,
    )
    return response


@with_params
def superset_view(request, dashboard_name, context):
    dashboard = get_object_or_404(Dashboard, short_name=dashboard_name)
    context["dashboard"] = serialize_dashboard(dashboard)
    filter_string = make_filter(
        dashboard,
        context["params"]["territory_id"],
        context["params"]["territory_mesh"],
    )
    if filter_string:
        context["dashboard_filter"] = filter_string
    response = render(
        request,
        "territories_dashboard_lib/website/pages/superset/page.html",
        context=context,
    )
    response = track_page(request=request, response=response)
    return response


def handler_404_view(request, exception):
    return render(request, "territories_dashboard_lib/website/404.html", status=404)


def handler_500_view(request):
    return render(request, "territories_dashboard_lib/website/500.html", status=500)


@gzip_page
def sitemap_view(request):
    context = {
        "themes": [
            {"title": theme.title, "name": theme.name}
            for theme in Theme.objects.all().order_by("ordering")
        ],
        "indicators": [
            {"title": indicator.title, "name": indicator.name}
            for indicator in Indicator.objects.all().order_by("index_in_theme")
        ],
        "static_pages": [
            {"title": static_page.name, "url": static_page.url}
            for static_page in StaticPage.objects.all()
        ],
        "lexique": GlossaryItem.objects.exists(),
    }
    response = render(
        request, "territories_dashboard_lib/website/pages/sitemap/page.html", context
    )
    response = track_page(request=request, response=response)
    return response
