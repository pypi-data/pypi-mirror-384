from ..enums import (
    FRANCE_DB_VALUES,
    MeshLevel,
)
from ..models import AggregationFunctions, Indicator
from .utils import get_breakdown_dimension, run_custom_query


def get_last_year(indicator, mesh):
    query = f""" SELECT MAX(annee) as last_year FROM "{indicator.db_table_prefix}_{mesh}" """
    return run_custom_query(query)[0]["last_year"]


def generate_aggregate_query(indicator, territory, submesh, filters, slicer):
    query = f"""
    WITH annee_max AS
    (SELECT MAX(annee) FROM "{indicator.db_table_prefix}_{submesh}"),
    aggregat AS
    (
        SELECT
        {calculate_aggregate_values(indicator)}, {slicer}
        FROM
        {get_table_data_for_geography(indicator, territory, submesh)}
        {add_optional_filters(indicator, filters)}
        AND annee = (SELECT * FROM annee_max)
        GROUP BY (indic.{slicer})
    )
    """
    return query


def generate_aggregate_query_for_location(indicator, territory, submesh, filters):
    return generate_aggregate_query(
        indicator, territory, submesh, filters, f"code_{submesh}"
    )


def add_optional_filters(indicator: Indicator, filters):
    condition = ""
    all_dimensions = [dimension.db_name for dimension in indicator.dimensions.all()]
    for dimension in all_dimensions:
        if filters and filters.get(dimension):
            filters_str = ", ".join(
                [f"'{value.replace("'", "''")}'" for value in filters.get(dimension)]
            )
            condition += f' AND indic."{dimension}" in ({filters_str}) '
    return condition


def get_place_names_join(include_place_name, mapped_submesh, submesh, flows=False):
    join_clause = ""
    if include_place_name:
        if flows:
            join_clause = f"""
            JOIN
                (SELECT distinct("NOM_{mapped_submesh}") as territory_1, "{mapped_submesh}" as territory_1_id, "{mapped_submesh}" from arborescence_geo) arbo1
                on arbo1."{mapped_submesh}" = indic.code_{submesh.lower()}_1
            JOIN
                (SELECT distinct("NOM_{mapped_submesh}") as territory_2, "{mapped_submesh}" as territory_2_id, "{mapped_submesh}" from arborescence_geo) arbo2
                on arbo2."{mapped_submesh}" = indic.code_{submesh.lower()}_2
            """
        else:
            join_clause = f"""
                JOIN
                (SELECT distinct("NOM_{mapped_submesh}") as lieu, "{mapped_submesh}" as territoryid, "{mapped_submesh}" from arborescence_geo) arbo
                on arbo."{mapped_submesh}" = indic.code_{submesh.lower()}
            """
    return join_clause


def get_table_data_for_geography(
    indicator,
    territory,
    submesh=MeshLevel.Region,
    include_place_names=None,
    flows=False,
):
    mapped_mesh = "DEPCOM" if territory.mesh == "com" else territory.mesh.upper()
    mapped_submesh = "DEPCOM" if submesh == "com" else submesh.upper()

    geo_id_values = "', '".join([id.strip() for id in territory.id.split(",")])

    table_prefix = (
        indicator.flows_db_table_prefix if flows else indicator.db_table_prefix
    )

    arbo_sub_query = f"""
    SELECT DISTINCT("{mapped_submesh}")
    FROM arborescence_geo arbo
    WHERE arbo."{mapped_mesh}" in('{geo_id_values}')
    """

    where = (
        f"""
        WHERE (indic.code_{submesh.lower()}_1 in ({arbo_sub_query})
        OR indic.code_{submesh.lower()}_2 in ({arbo_sub_query}))
        """
        if flows
        else f"""
        WHERE indic.code_{submesh.lower()} in ({arbo_sub_query})
        """
    )

    return f"""
    "{table_prefix}_{submesh.lower()}" indic
    {get_place_names_join(include_place_names, mapped_submesh, submesh, flows)}
    {where}
    """


def calculate_aggregate_values(indicator, with_alternative=True):
    # TODO coverage tester avec un indicateur de cette sorte
    # Bastien doit exporter des nouvelles données pour faire le test
    if not indicator.is_composite:
        return "SUM(valeur) as valeur"

    # TODO coverage tester avec un indicateur de cette sorte
    # Bastien doit exporter des nouvelles données pour faire le test
    if indicator.aggregation_function == AggregationFunctions.DISCRETE_COMPONENT_2:
        sql = f"SUM(composante_1) / COALESCE(NULLIF(SUM(composante_2), 0), 1) * {indicator.aggregation_constant} as valeur"
        if with_alternative:
            sql += ", SUM(composante_1) as valeur_alternative"
        return sql
    breakdown_dimension = get_breakdown_dimension(indicator)
    breakdown_count = (
        f" * COUNT(DISTINCT({breakdown_dimension.db_name})) "
        if breakdown_dimension
        else ""
    )
    sql = f"SUM(composante_1) / COALESCE(NULLIF(SUM(composante_2), 0), 1) {breakdown_count} * {indicator.aggregation_constant} as valeur"
    if with_alternative:
        sql += ", SUM(composante_1) as valeur_alternative"
    return sql


def get_territories_ids(main_territory_codes, territory_mesh, submesh):
    mapped_territory_mesh = (
        "DEPCOM" if territory_mesh == "com" else territory_mesh.upper()
    )
    mapped_submesh = "DEPCOM" if submesh == "com" else submesh.upper()

    query = f"""
        SELECT DISTINCT "{mapped_submesh}" as code
        FROM arborescence_geo
        WHERE "{mapped_territory_mesh}" IN ('{"', '".join(main_territory_codes)}')
        """

    territories_ids = [r["code"] for r in run_custom_query(query)]
    return territories_ids


def get_sub_territories(territory, submesh):
    territory_codes = territory.id.split(",")
    mapped_territory_mesh = (
        "DEPCOM" if territory.mesh == "com" else territory.mesh.upper()
    )
    mapped_submesh = "DEPCOM" if submesh == "com" else submesh.upper()

    query = f"""
        SELECT DISTINCT "{mapped_submesh}" as code, "NOM_{mapped_submesh}" as name
        FROM arborescence_geo
        WHERE "{mapped_territory_mesh}" IN ('{"', '".join(territory_codes)}')
        """

    return run_custom_query(query)


def get_where_territory(territory):
    territory_id = (
        FRANCE_DB_VALUES[territory.id]
        if territory.mesh == MeshLevel.National
        else territory.id
    )
    return f""" "code_{territory.mesh}" = '{territory_id}' """


def get_values_for_territory(indicator, territory, filters=None):
    value = calculate_aggregate_values(indicator)
    where_territory = get_where_territory(territory)
    query = f"""
        SELECT {value}, annee
        FROM "{indicator.db_table_prefix}_{territory.mesh}" as indic
        WHERE {where_territory}
        {add_optional_filters(indicator, filters)}
        GROUP BY annee
        ORDER BY annee DESC
    """
    return query


def get_territory_name(territory):
    territory_mesh = "DEPCOM" if territory.mesh == "com" else territory.mesh.upper()
    query = f"""SELECT "NOM_{territory_mesh}" as nom FROM arborescence_geo WHERE "{territory_mesh}" = '{territory.id}' LIMIT 1;"""
    results = run_custom_query(query)
    return results[0]["nom"] if results else ""
