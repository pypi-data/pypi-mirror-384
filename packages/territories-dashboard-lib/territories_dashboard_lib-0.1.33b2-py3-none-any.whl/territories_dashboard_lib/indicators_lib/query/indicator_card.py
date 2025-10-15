from .commons import generate_aggregate_query_for_location
from .utils import run_custom_query


def generate_min_max_queries(indicator):
    result = """
    , min_value AS (SELECT MIN(valeur) AS min FROM aggregat),
    max_value AS (SELECT MAX(valeur) AS max FROM aggregat)
    """
    if indicator.is_composite:
        result += """
        , min_alternative_value AS (SELECT MIN(valeur_alternative) AS min_alternative FROM aggregat),
        max_alternative_value AS (SELECT MAX(valeur_alternative) AS max_alternative FROM aggregat)
        """
    return result


def get_min_max_statistics(indicator, submesh):
    result = f"""
    {get_values_for("min", submesh)}
    {get_values_for("max", submesh)}
    """
    if indicator.is_composite:
        result += f"""
        {get_values_for("min_alternative", submesh, True)}
        {get_values_for("max_alternative", submesh, True)}
        """
    return result


def get_values_for(extremum, submesh, is_alternative=False):
    return f"""
    {extremum}_value,
    (
        SELECT code_{submesh} AS code_{extremum}
        FROM aggregat
        WHERE valeur{"_alternative" if is_alternative else ""} = (SELECT * FROM {extremum}_value) LIMIT 1
    ) AS code_{extremum},
    (
        SELECT count(code_{submesh}) AS count_{extremum}
        FROM aggregat
        WHERE valeur{"_alternative" if is_alternative else ""} = (SELECT * FROM {extremum}_value)
    ) AS count_{extremum},
    """


def get_med_values(indicator):
    return f"""
    (SELECT
    PERCENTILE_DISC(0.5) WITHIN GROUP (order by valeur) AS med
    {", PERCENTILE_DISC(0.5) WITHIN GROUP (order by valeur_alternative) AS med_alternative" if indicator.is_composite else ""}
    FROM aggregat) AS meds
    """


def get_geography_statistics_values_for_indicator(
    indicator, territory, submesh, filters
):
    query = f"""
    {generate_aggregate_query_for_location(indicator, territory, submesh, filters)}
    {generate_min_max_queries(indicator)}

    SELECT * FROM
    {get_min_max_statistics(indicator, submesh)}
    {get_med_values(indicator)}
    """

    return query


def get_names_from_codes(dict_result, submesh):
    codes_to_fetch = []
    for key, value in dict_result.items():
        if key.startswith("code_"):
            codes_to_fetch.append(value)
    mapped_submesh = "DEPCOM" if submesh == "com" else submesh.upper()
    query = f"""
    SELECT DISTINCT "{mapped_submesh}" as code, "NOM_{mapped_submesh}" as name
    FROM arborescence_geo
    WHERE "{mapped_submesh}" IN ({", ".join(["'" + c + "'" for c in codes_to_fetch])});
    """
    rows = run_custom_query(query)
    names_dict = {}
    for row in rows:
        names_dict[row["code"]] = row["name"]
    updated_dict = {}
    for key, value in dict_result.items():
        updated_dict[key] = value
        if key.startswith("code_"):
            updated_dict[key + "_name"] = names_dict[value]
    return updated_dict
