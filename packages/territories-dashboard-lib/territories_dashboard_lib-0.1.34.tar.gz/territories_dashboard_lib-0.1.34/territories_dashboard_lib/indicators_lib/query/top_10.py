from collections import defaultdict

from .commons import (
    add_optional_filters,
    calculate_aggregate_values,
    get_last_year,
    get_table_data_for_geography,
)
from .utils import get_breakdown_dimension, run_custom_query


def breakdown_territories(indicator, submesh, year, filters, top_10_territories):
    territories_code = ", ".join(
        [f"'{territory['code_geo']}'" for territory in top_10_territories]
    )
    breakdown_dimension = get_breakdown_dimension(indicator).db_name

    query = f"""
        SELECT {calculate_aggregate_values(indicator, with_alternative=False)},
            "{breakdown_dimension}" as dimension,
            "code_{submesh}" as code_geo
        FROM "{indicator.db_table_prefix}_{submesh}" as indic
        WHERE code_{submesh} in ({territories_code}) AND annee = {year}
        {add_optional_filters(indicator, filters)}
        GROUP BY "code_{submesh}", "{breakdown_dimension}"
    """
    results = run_custom_query(query)
    return results


def get_top_10_territories(indicator, territory, submesh, year, filters):
    query = f"""
    SELECT {calculate_aggregate_values(indicator, with_alternative=False)},
    indic.code_{submesh} as code_geo, arbo.lieu as lieu
    FROM {get_table_data_for_geography(indicator, territory, submesh, include_place_names=True)}
    {add_optional_filters(indicator, filters)}
    AND annee = {year}
    GROUP BY code_{submesh}, arbo.lieu
    ORDER BY valeur DESC
    LIMIT 10
    """
    results = run_custom_query(query)
    return results


def get_indicator_top_10_data(indicator, territory, submesh, filters):
    indicator_details = {}

    breakdown_dimension = get_breakdown_dimension(indicator)
    breakdown_dimension_name = (
        breakdown_dimension.db_name if breakdown_dimension else None
    )
    breakdown_filters = filters.get(breakdown_dimension_name, [])

    last_year = get_last_year(indicator, submesh)

    territories = get_top_10_territories(
        indicator, territory, submesh, last_year, filters
    )

    if breakdown_dimension:
        breakdown = breakdown_territories(
            indicator, submesh, last_year, filters, territories
        )
        breakdown_by_geocode = defaultdict(dict)
        for row in breakdown:
            breakdown_by_geocode[row["code_geo"]][row["dimension"]] = row["valeur"]
        filters_color = {f.db_name: f.color for f in breakdown_dimension.filters.all()}
        datasets_top_bar_chart = [
            {
                "label": f,
                "data": [
                    breakdown_by_geocode[territory["code_geo"]][f]
                    for territory in territories
                ],
                "color": filters_color.get(f),
            }
            for f in breakdown_filters
        ]
    # TODO coverage faire un test avec un indicateur qui n'a pas de dimensions
    # necessite un export de données de Bastien
    else:
        datasets_top_bar_chart = [
            {
                "label": indicator.unite,
                "data": [territory["valeur"] for territory in territories],
            }
        ]

    labels_top_bar_chart = [territory["lieu"] for territory in territories]

    csv_data = []
    for territory in territories:
        csv_row = {}
        csv_row["Territoire"] = territory["lieu"]
        csv_row["Code Géographique"] = territory["code_geo"]
        csv_row[f"Valeur {indicator.unite}"] = territory["valeur"]
        if breakdown_dimension:
            for filter in breakdown_filters:
                csv_row[filter] = breakdown_by_geocode[territory["code_geo"]][filter]
        csv_data.append(csv_row)

    indicator_details["labelsTopBarChart"] = labels_top_bar_chart
    indicator_details["datasetsTopBarChart"] = datasets_top_bar_chart

    return indicator_details, csv_data
