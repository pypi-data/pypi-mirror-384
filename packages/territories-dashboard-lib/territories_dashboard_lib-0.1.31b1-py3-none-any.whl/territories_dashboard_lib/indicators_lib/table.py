from .payloads import IndicatorTablePayload
from .query.commons import add_optional_filters, get_table_data_for_geography
from .query.utils import run_custom_query


def _get_query(
    *, indicator, props: IndicatorTablePayload, columns, orders, filters, limit=None
):
    columns = [c for c in columns if c is not None]
    orders = [o for o in orders if o is not None]
    order_clause = f"ORDER BY {', '.join(orders)}" if len(orders) > 0 else ""
    limitation = f"LIMIT {limit}" if limit is not None else ""
    offset = f"OFFSET {(props.pagination - 1) * limit}" if limit is not None else ""
    dimension_search_where = (
        f"OR (unaccent(LOWER({indicator.flows_dimension})) LIKE unaccent(LOWER(CONCAT('%%', %(search)s, '%%'))))"
        if props.flows
        else " ".join(
            [
                f"OR (unaccent(LOWER({dimension.db_name})) LIKE unaccent(LOWER(CONCAT('%%', %(search)s, '%%'))))"
                for dimension in indicator.dimensions.all()
            ]
        )
    )
    territory_search_where = (
        "OR (unaccent(LOWER(territory_1)) LIKE unaccent(LOWER(CONCAT('%%', %(search)s, '%%')))) OR (unaccent(LOWER(territory_2)) LIKE unaccent(LOWER(CONCAT('%%', %(search)s, '%%'))))"
        if props.flows
        else (
            "OR (unaccent(LOWER(lieu)) LIKE unaccent(LOWER(CONCAT('%%', %(search)s, '%%'))))"
        )
    )
    where = (
        f"""
        AND (
            (LENGTH(TRIM(%(search)s)) = 0)
            {territory_search_where}
            {dimension_search_where}
            OR (CAST(annee AS TEXT) LIKE CONCAT('%%', %(search)s, '%%'))
        )
    """
        if props.search
        else ""
    )
    where_year = f"AND annee = {props.year}" if props.year else ""
    regular_dimensions_filters = (
        "" if props.flows else add_optional_filters(indicator, filters)
    )
    return f"""
        SELECT
            {", ".join(columns)}
        FROM
            {get_table_data_for_geography(indicator, props.territory, props.submesh, True, props.flows)}
            {regular_dimensions_filters}
        {where} {where_year}
        {order_clause}
        {f"{limitation} {offset}"}
    """


def get_values_columns(indicator, props, *, for_export=False):
    if props.flows:
        columns = [
            "annee",
            "territory_1",
            "territory_2",
            f"{indicator.flows_dimension} AS dimension"
            if indicator.flows_dimension
            else None,
            "CAST(valeur AS int) as valeur",
        ]
        if for_export:
            columns += ["territory_1_id", "territory_2_id"]
    else:
        columns = (
            ["annee", "lieu"]
            + [f"{dimension.db_name}" for dimension in indicator.dimensions.all()]
            + [
                f"valeur * {indicator.aggregation_constant if indicator.unite == '%' else 1} AS valeur",
                "CASE WHEN valeur IS NULL THEN NULL ELSE composante_1 END AS valeur_alternative"
                if indicator.is_composite and indicator.show_alternative
                else None,
            ]
        )
        if for_export:
            columns += ["territoryid"]
    return columns


def get_values_orders(indicator, props: IndicatorTablePayload):
    territory_order = None
    if props.column_order not in ["lieu", "territory_1", "territory_2"]:
        territory_order = (
            "LOWER(territory_1) ASC, LOWER(territory_2) ASC"
            if props.flows
            else "LOWER(lieu) ASC"
        )
    year_order = "annee DESC" if props.column_order != "annee" else None
    dimension_order = None
    if props.flows:
        dimension = indicator.flows_dimension
        if props.column_order != dimension:
            dimension_order = f"{dimension} DESC"
    else:
        dimensions = [dimension.db_name for dimension in indicator.dimensions.all()]
        if props.column_order not in [dimensions]:
            dimension_order = (
                ", ".join([f"{dimension} DESC" for dimension in dimensions])
                if dimensions
                else None
            )
    orders = [
        f"{props.column_order} {props.column_order_flow} NULLS LAST"
        if props.column_order
        else None,
        year_order,
        territory_order,
        dimension_order,
    ]
    return orders


def get_count_and_data_for_indicator_table(
    indicator, props: IndicatorTablePayload, filters
):
    count_query = _get_query(
        indicator=indicator,
        props=props,
        columns=["COUNT(*)"],
        orders=[],
        filters=filters,
    )
    count = run_custom_query(count_query, {"search": props.search})
    columns = get_values_columns(indicator, props)
    orders = get_values_orders(indicator, props)
    data_query = _get_query(
        indicator=indicator,
        props=props,
        columns=columns,
        orders=orders,
        limit=props.limit,
        filters=filters,
    )
    data = run_custom_query(data_query, {"search": props.search})
    return count[0]["count"], data


def get_export_indicator_table_values(indicator, props: IndicatorTablePayload, filters):
    query = _get_query(
        indicator=indicator,
        props=props,
        columns=get_values_columns(indicator, props, for_export=True),
        orders=get_values_orders(indicator, props),
        filters=filters,
    )
    return run_custom_query(query, {"search": props.search})
