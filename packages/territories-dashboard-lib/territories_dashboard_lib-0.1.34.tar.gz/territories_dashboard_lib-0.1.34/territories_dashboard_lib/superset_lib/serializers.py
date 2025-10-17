from .models import Dashboard


def serialize_dashboard(dashboard: Dashboard):
    return {
        "id": dashboard.id,
        "superset_id": dashboard.superset_id,
        "label": dashboard.label,
        "short_name": dashboard.short_name,
    }
