from django.conf import settings

from territories_dashboard_lib.superset_lib.models import Dashboard
from territories_dashboard_lib.superset_lib.serializers import serialize_dashboard
from territories_dashboard_lib.website_lib.models import (
    MainConf,
    NoticeBanner,
)


def default(request):
    main_conf = MainConf.objects.first()
    notice = NoticeBanner.objects.first()
    context = {
        "ENABLE_SUPERSET": settings.ENABLE_SUPERSET,
        "ANALYTICS_ID": settings.ANALYTICS_ID,
        "ENVIRONMENT": settings.ENVIRONMENT,
        "view_name": request.resolver_match.view_name,
        "absolute_uri": request.build_absolute_uri(),
        "main_conf": main_conf,
        "notice": notice,
        "dashboards": [
            serialize_dashboard(d)
            for d in Dashboard.objects.all().order_by("order", "label")
        ],
        "version": settings.VERSION,
    }
    return context
