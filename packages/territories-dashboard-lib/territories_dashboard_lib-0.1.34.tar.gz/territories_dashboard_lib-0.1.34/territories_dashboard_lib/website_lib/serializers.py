from django.db.models import Count, Q
from martor.utils import markdownify


def serialize_indicator(indicator):
    return {
        "id": indicator.id,
        "name": indicator.name,
        "title": indicator.title,
        "short_title": indicator.short_title,
        "description": indicator.description,
        "source": indicator.source,
        "unite": indicator.unite,
        "unite_nom_accessible": indicator.unite_nom_accessible,
        "unite_alternative": indicator.unite_alternative,
        "unite_alternative_nom_accessible": indicator.unite_alternative_nom_accessible,
        "show_alternative": indicator.show_alternative,
        "methodo_html": markdownify(indicator.methodo),
        "db_table_prefix": indicator.db_table_prefix,
        "is_composite": indicator.is_composite,
        "aggregation_constant": indicator.aggregation_constant,
        "flows_db_table_prefix": indicator.flows_db_table_prefix,
        "flows_dimension": indicator.flows_dimension,
        "theme": indicator.sub_theme.theme.title,
        "filters": serializer_filters(indicator),
        "show_evolution": indicator.show_evolution,
        "min_mesh": indicator.min_mesh,
        "secondary_indicator": {
            "name": indicator.secondary_indicator.name,
            "title": indicator.secondary_indicator.title,
            "short_title": indicator.secondary_indicator.short_title,
            "aggregation_constant": indicator.secondary_indicator.aggregation_constant,
            "db_table_prefix": indicator.secondary_indicator.db_table_prefix,
            "unite": indicator.secondary_indicator.unite,
            "unite_alternative": indicator.secondary_indicator.unite_alternative,
            "is_composite": indicator.secondary_indicator.is_composite,
            "filters": serializer_filters(indicator.secondary_indicator),
        }
        if indicator.secondary_indicator
        else None,
        "geo_features": [
            {
                "id": gf.id,
                "name": gf.name,
                "title": gf.title,
                "unite": gf.unite,
                "geo_type": gf.geo_type,
                "point_icon_svg": gf.point_icon_svg,
                "color": gf.color,
                "show_on_fr_level": gf.show_on_fr_level,
                "items": [
                    {
                        "name": item.name,
                        "label": item.label,
                        "filterable": item.filterable,
                    }
                    for item in gf.items.all()
                ],
            }
            for gf in indicator.geo_features.all()
        ],
    }


def serializer_filters(indicator):
    return [
        (
            {
                "db_name": dimension.db_name,
                "title": dimension.title,
                "is_breakdown": dimension.is_breakdown,
            },
            [
                {
                    "db_name": filtr.db_name,
                    "default": filtr.default,
                }
                for filtr in dimension.filters.all()
            ],
        )
        for dimension in indicator.dimensions.all()
    ]


def serialize_sub_themes(theme):
    sub_themes = (
        theme.sub_themes.all()
        .annotate(
            active_indicators_count=Count(
                "indicators", filter=Q(indicators__is_active=True)
            )
        )
        .filter(active_indicators_count__gt=0)
        .order_by("index_in_theme")
    )
    sub_themes = [
        {
            "name": sub_theme.name,
            "title": sub_theme.title,
            "indicators": [
                serialize_indicator(indicator)
                for indicator in sub_theme.indicators.filter(is_active=True).order_by(
                    "index_in_theme"
                )
            ],
        }
        for sub_theme in sub_themes
    ]
    return sub_themes
