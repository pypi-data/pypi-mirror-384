from .details import get_values_for_submesh_territories


def get_territories_histogram_data(territory_values, unite):
    if all([t["valeur"] is None for t in territory_values]):
        return ({}, [])
    values_for_min_max = [
        data["valeur"] for data in territory_values if data["valeur"] is not None
    ]
    min_value_last_year = min(values_for_min_max) if values_for_min_max else 0
    max_value_last_year = max(values_for_min_max) if values_for_min_max else 0

    # if we are between 99.5 and 100.5, spread histogram for better visualization
    if 99.5 < min_value_last_year < 100.5 and 99.5 < max_value_last_year < 100.5:
        min_value_last_year = 90

    histogram_values_dict = {}
    for territory_data in territory_values:
        territory_id = territory_data["geocode"]
        if territory_id not in histogram_values_dict:
            histogram_values_dict[territory_id] = {
                "valeur": 0,
                "geoname": territory_data["geoname"],
            }
        histogram_values_dict[territory_id]["valeur"] += (
            territory_data["valeur"] if territory_data["valeur"] is not None else 0
        )
    histogram_values = list(histogram_values_dict.values())

    deciles = [
        min_value_last_year + (max_value_last_year - min_value_last_year) * (i / 10)
        for i in range(10 if min_value_last_year != max_value_last_year else 1)
    ]

    data_by_decile = [
        {
            "decile": decile,
            "count": len(
                [
                    data
                    for data in histogram_values
                    if decile
                    <= data["valeur"]
                    <= (deciles[i + 1] if i < len(deciles) - 1 else max_value_last_year)
                ]
            ),
            "text": "\n".join(
                [
                    data["geoname"]
                    for data in histogram_values
                    if decile
                    <= data["valeur"]
                    <= (deciles[i + 1] if i < len(deciles) - 1 else max_value_last_year)
                ]
            ),
        }
        for i, decile in enumerate(deciles)
    ]

    datasets_histogram_bar_chart = {
        "label": unite,
        "data": [{"x": data["decile"], "y": data["count"]} for data in data_by_decile],
        "comments": [data["text"] for data in data_by_decile],
        "backgroundColor": "#6a6af4",
    }

    return (datasets_histogram_bar_chart, deciles)


def get_indicator_histogram_data(indicator, territory, submesh, filters):
    indicator_details = {}
    territory_values = get_values_for_submesh_territories(
        indicator, submesh, territory, filters
    )
    datasets_histogram_bar_chart, deciles = get_territories_histogram_data(
        territory_values, indicator.unite
    )

    indicator_details["datasetsHistogramBarChart"] = datasets_histogram_bar_chart
    indicator_details["deciles"] = deciles

    return indicator_details
