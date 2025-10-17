from collections import defaultdict

from .commons import add_optional_filters, calculate_aggregate_values
from .utils import run_custom_query


def get_comparison_values_and_buckets(
    indicator, submesh, territories, cmp_territories, filters
):
    territories_ids = [t["code"] for t in territories + cmp_territories]
    territories_sql = f"('{"', '".join(territories_ids)}')"
    table_name = f"{indicator.db_table_prefix}_{submesh}"
    filters = add_optional_filters(indicator, filters)
    value = calculate_aggregate_values(indicator, with_alternative=False)
    number_of_buckets = min(10, len(territories) + len(cmp_territories))
    sub_query = f"""
    SELECT
        {value},
        code_{submesh} as geo_code
    FROM {table_name} indic
    WHERE code_{submesh} IN {territories_sql}
    AND annee = (
        SELECT MAX(annee)
        FROM {table_name}
    )
    AND valeur IS NOT NULL
    {filters}
    GROUP BY geo_code
    """
    query = f"""
    WITH aggregated_data AS ({sub_query}),
    range_bounds AS (
        SELECT
            MIN(valeur) - 1e-10 AS min_value,
            MAX(valeur) + 1e-10 AS max_value
        FROM aggregated_data
    )
    SELECT
        aggregated_data.valeur,
        aggregated_data.geo_code,
        WIDTH_BUCKET(aggregated_data.valeur, range_bounds.min_value, range_bounds.max_value, {number_of_buckets}) AS bucket
    FROM aggregated_data
    CROSS JOIN
        range_bounds
    """
    results = run_custom_query(query)
    raw_values = [r["valeur"] for r in results]
    min_value = min(raw_values)
    max_value = max(raw_values)
    bucket_width = (max_value - min_value) / number_of_buckets
    buckets = []
    bucket_min = min_value
    for i in range(1, number_of_buckets + 1):
        bucket_max = (
            max_value if i == number_of_buckets else min_value + i * bucket_width
        )
        buckets.append([bucket_min, bucket_max])
        bucket_min = bucket_max
    values = defaultdict(list)
    cmp_values = defaultdict(list)
    territories_ids_set = {t["code"] for t in territories}
    cmp_territories_ids_set = {t["code"] for t in cmp_territories}
    territories_dict = {t["code"]: t["name"] for t in territories + cmp_territories}
    for r in results:
        geo_code = r["geo_code"]
        if geo_code in territories_ids_set:
            values[r["bucket"]].append(territories_dict[geo_code])
        if geo_code in cmp_territories_ids_set:
            cmp_values[r["bucket"]].append(territories_dict[geo_code])
    return values, cmp_values, buckets
