import json

from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

from territories_dashboard_lib.commons.decorators import use_payload
from territories_dashboard_lib.tracking_lib.enums import EventType, GraphType
from territories_dashboard_lib.tracking_lib.logic import track_event

from .enums import MESH_TITLES
from .export import export_to_csv
from .format import format_data, format_indicator_value
from .models import Indicator
from .payloads import (
    BasePayload,
    ComparisonQueryPayload,
    FlowsPayload,
    IndicatorTablePayload,
    OptionalComparisonQueryPayload,
    SubMeshPayload,
)
from .query.commons import (
    get_sub_territories,
    get_territory_name,
    get_values_for_territory,
)
from .query.comparison import get_comparison_values_and_buckets
from .query.details import get_proportions_chart, get_values_for_submesh_territories
from .query.histogram import get_indicator_histogram_data
from .query.indicator_card import (
    get_geography_statistics_values_for_indicator,
    get_names_from_codes,
)
from .query.top_10 import get_indicator_top_10_data
from .query.utils import run_custom_query
from .table import (
    get_count_and_data_for_indicator_table,
    get_export_indicator_table_values,
)


def download_indicator_methodo_view(request, name):
    """View to download the methodology file for an indicator."""
    indicator = get_object_or_404(Indicator, name=name)

    if not indicator.methodo_file:
        raise Http404("No methodology file available for this indicator.")

    response = HttpResponse(indicator.methodo_file, content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=methodo.pdf"
    response = track_event(
        request=request,
        response=response,
        event_name=EventType.download,
        data={"indicator": indicator.name, "objet": "methodo", "type": "pdf"},
    )
    return response


@cache_control(max_age=3600)
@use_payload(SubMeshPayload)
def indicator_statistics_view(request, name, payload):
    indicator = get_object_or_404(Indicator, name=name)
    filters = get_filters(request, indicator)
    query = get_geography_statistics_values_for_indicator(
        indicator,
        payload.territory,
        payload.submesh,
        filters,
    )
    rows = run_custom_query(query)
    if not rows:
        return HttpResponse("{}")
    data = rows[0]
    data = get_names_from_codes(data, payload.submesh)
    return HttpResponse(json.dumps(data))


def get_values(indicator, payload, filters):
    query = get_values_for_territory(
        indicator,
        payload.territory,
        filters,
    )
    rows = run_custom_query(query)
    results = {"values": rows}
    if payload.cmp_territory:
        query = get_values_for_territory(
            indicator,
            payload.cmp_territory,
            filters,
        )
        cmp_rows = run_custom_query(query)
        results["cmp_values"] = cmp_rows
    return results


def get_filters(request, indicator):
    filters = {}
    for dimension in indicator.dimensions.all():
        input_filters = request.GET.getlist(dimension.db_name)
        possible_filters = [f.db_name for f in dimension.filters.all()]
        filters[dimension.db_name] = [f for f in input_filters if f in possible_filters]
    return filters


@require_GET
@cache_control(max_age=3600)
@use_payload(OptionalComparisonQueryPayload)
def indicator_values_view(request, name, payload):
    indicator = get_object_or_404(Indicator, name=name)
    filters = get_filters(request, indicator)
    results = get_values(indicator, payload, filters)
    return HttpResponse(json.dumps(results))


@require_GET
@use_payload(OptionalComparisonQueryPayload)
def indicator_values_export_view(request, name, payload):
    indicator = get_object_or_404(Indicator, name=name)
    filters = get_filters(request, indicator)
    results = get_values(indicator, payload, filters)
    export_values = {}
    territory_name = get_territory_name(payload.territory)
    for value in results["values"]:
        export_values[value["annee"]] = {
            "Année": value["annee"],
            f"Valeur {territory_name} ({indicator.unite})": value["valeur"],
        }
        if indicator.unite_alternative and "valeur_alternative" in value:
            export_values[value["annee"]][
                f"Valeur {territory_name} ({indicator.unite_alternative})"
            ] = value["valeur_alternative"]
    tracking_objet = "historique"
    if results.get("cmp_values") is not None:
        cmp_territory_name = get_territory_name(payload.cmp_territory)
        for value in results["cmp_values"]:
            export_values[value["annee"]][
                f"Valeur {cmp_territory_name} ({indicator.unite})"
            ] = value["valeur"]
        tracking_objet = "comparaison-" + tracking_objet
    return export_to_csv(
        request, indicator, tracking_objet, list(export_values.values())
    )


@require_GET
@cache_control(max_age=3600)
@use_payload(SubMeshPayload)
def indicator_submesh_territories_view(request, name, payload):
    indicator = get_object_or_404(Indicator, name=name)
    filters = get_filters(request, indicator)
    data = get_values_for_submesh_territories(
        indicator, payload.submesh, payload.territory, filters
    )
    return HttpResponse(json.dumps(data))


@cache_control(max_age=3600)
@use_payload(BasePayload)
def proportions_chart_view(request, name, payload):
    indicator = get_object_or_404(Indicator, name=name)
    if indicator.dimensions.count() == 0:
        return HttpResponse(status=400)
    filters = get_filters(request, indicator)
    rows = get_proportions_chart(
        indicator,
        payload.territory,
        filters,
    )
    return HttpResponse(json.dumps({"values": rows}))


@require_GET
@use_payload(BasePayload)
def indicator_proportions_export_view(request, name, payload):
    indicator = get_object_or_404(Indicator, name=name)
    if indicator.dimensions.count() == 0:
        return HttpResponse(status=400)
    filters = get_filters(request, indicator)
    rows = get_proportions_chart(
        indicator,
        payload.territory,
        filters,
    )
    rows = [
        {"Dimension": r["label"], f"Valeur {indicator.unite}": r["data"][0]}
        for r in rows
    ]
    return export_to_csv(request, indicator, GraphType.repartition_dimension, rows)


@cache_control(max_age=3600)
@use_payload(SubMeshPayload)
def indicator_histogram_view(request, name, payload):
    indicator = get_object_or_404(Indicator, name=name)
    filters = get_filters(request, indicator)
    data = get_indicator_histogram_data(
        indicator,
        payload.territory,
        payload.submesh,
        filters,
    )
    return HttpResponse(json.dumps(data))


@cache_control(max_age=3600)
@use_payload(SubMeshPayload)
def indicator_histogram_export_view(request, name, payload):
    indicator = get_object_or_404(Indicator, name=name)
    filters = get_filters(request, indicator)
    data = get_indicator_histogram_data(
        indicator,
        payload.territory,
        payload.submesh,
        filters,
    )
    rows = []
    for index, decile in enumerate(data["deciles"]):
        row = {}
        next_decile = (
            format_indicator_value(data["deciles"][index + 1])
            if index < len(data["deciles"]) - 1
            else "+"
        )
        row["Décile"] = f"{format_indicator_value(decile)} - {next_decile}"
        row["Nombre de territoires"] = data["datasetsHistogramBarChart"]["data"][index][
            "y"
        ]
        row["Commentaire"] = data["datasetsHistogramBarChart"]["comments"][
            index
        ].replace("\n", " | ")
        rows.append(row)
    return export_to_csv(request, indicator, GraphType.repartition_valeurs, rows)


@cache_control(max_age=3600)
@use_payload(SubMeshPayload)
def indicator_top_10_view(request, name, payload):
    indicator = get_object_or_404(Indicator, name=name)
    filters = get_filters(request, indicator)
    data, _ = get_indicator_top_10_data(
        indicator,
        payload.territory,
        payload.submesh,
        filters,
    )
    return HttpResponse(json.dumps(data))


@require_GET
@use_payload(SubMeshPayload)
def indicator_top_10_export_view(request, name, payload):
    indicator = get_object_or_404(Indicator, name=name)
    filters = get_filters(request, indicator)
    _, csv_data = get_indicator_top_10_data(
        indicator,
        payload.territory,
        payload.submesh,
        filters,
    )
    return export_to_csv(request, indicator, GraphType.top_10, csv_data)


@require_GET
@cache_control(max_age=3600)
@use_payload(FlowsPayload)
def flows_view(request, payload):
    flows_table = f"{payload.prefix}_{payload.submesh}"

    # Query to get the latest year
    last_year_query = f"SELECT DISTINCT annee FROM {flows_table} ORDER BY annee DESC"
    last_year = run_custom_query(last_year_query)[0]["annee"]

    mapped_geo_level = (
        "DEPCOM" if payload.territory.mesh == "com" else payload.territory.mesh.upper()
    )
    mapped_mesh_level = (
        "DEPCOM" if payload.submesh == "com" else payload.submesh.upper()
    )

    codes = ", ".join(f"'{code.strip()}'" for code in payload.territory.id.split(","))

    # Geo query
    geo_query = f"""
        SELECT DISTINCT
            arbo."{mapped_mesh_level}" as territory_id,
            arbo."NOM_{mapped_mesh_level}" as territory_name,
            ST_ASGEOJSON(ST_CENTROID(contours.geometry)) as center
        FROM arborescence_geo AS arbo
        JOIN contours_simplified_{payload.submesh} as contours
        ON arbo."{mapped_mesh_level}" = contours.code
        WHERE arbo."{mapped_geo_level}" IN ({codes})
    """
    territories = run_custom_query(geo_query)
    territories_ids = ", ".join(f"'{t['territory_id'].strip()}'" for t in territories)

    dimension_value = (
        f"{payload.dimension} as dimension"
        if payload.dimension
        else "'all' as dimension"
    )

    # Values query
    values_query = f"""
        SELECT
            code_{payload.submesh}_1 as territory_1_id,
            code_{payload.submesh}_2 as territory_2_id,
            CAST(valeur AS int) as value,
            {dimension_value}
        FROM {flows_table} flows
        WHERE annee = {last_year}
        AND (
            code_{payload.submesh}_1 IN ({territories_ids})
            OR code_{payload.submesh}_2 IN ({territories_ids})
        )
    """
    row_values = run_custom_query(values_query)
    territories_dict = {
        t["territory_id"]: {
            "name": t["territory_name"],
            "code": t["territory_id"],
            "center": json.loads(t["center"]),
        }
        for t in territories
    }

    external_territories_ids = set()
    for row in row_values:
        if row["territory_1_id"] not in territories_dict:
            external_territories_ids.add(row["territory_1_id"])
        if row["territory_2_id"] not in territories_dict:
            external_territories_ids.add(row["territory_2_id"])
    external_territories_ids

    external_territories = []
    if external_territories_ids:
        codes = ", ".join([f"'{tid}'" for tid in external_territories_ids])
        geo_query = f"""
            SELECT DISTINCT
                arbo."{mapped_mesh_level}" as territory_id,
                arbo."NOM_{mapped_mesh_level}" as territory_name,
                ST_ASGEOJSON(ST_CENTROID(contours.geometry)) as center
            FROM arborescence_geo AS arbo
            JOIN contours_simplified_{payload.submesh} as contours
            ON arbo."{mapped_mesh_level}" = contours.code
            WHERE arbo."{mapped_mesh_level}" IN ({codes})
        """
        external_territories = run_custom_query(geo_query)
    for t in external_territories:
        territories_dict[t["territory_id"]] = {
            "name": f"{t['territory_name']} (externe)",
            "code": t["territory_id"],
            "center": json.loads(t["center"]),
        }

    return JsonResponse(
        {"flows": row_values, "territories": territories_dict}, status=200
    )


@require_GET
@cache_control(max_age=3600)
@use_payload(ComparisonQueryPayload)
def comparison_histogram_view(request, name, payload):
    indicator = get_object_or_404(Indicator, name=name)
    filters = get_filters(request, indicator)
    territories = get_sub_territories(payload.territory, payload.submesh)
    cmp_territories = get_sub_territories(payload.cmp_territory, payload.submesh)
    values, cmp_values, buckets = get_comparison_values_and_buckets(
        indicator, payload.submesh, territories, cmp_territories, filters
    )
    return JsonResponse(
        {
            "values": values,
            "comparedValues": cmp_values,
            "buckets": buckets,
        }
    )


@require_GET
@use_payload(ComparisonQueryPayload)
def comparison_histogram_export_view(request, name, payload):
    indicator = get_object_or_404(Indicator, name=name)
    filters = get_filters(request, indicator)
    territories = get_sub_territories(payload.territory, payload.submesh)
    cmp_territories = get_sub_territories(payload.cmp_territory, payload.submesh)
    values, cmp_values, buckets = get_comparison_values_and_buckets(
        indicator, payload.submesh, territories, cmp_territories, filters
    )
    rows = []
    territory_name = get_territory_name(payload.territory)
    cmp_territory_name = get_territory_name(payload.cmp_territory)
    for index, bucket in enumerate(buckets):
        row = {}
        row["Décile"] = (
            f"{format_indicator_value(bucket[0])} - {format_indicator_value(bucket[1])}"
        )
        row[f"{territory_name} - Nombre de {MESH_TITLES[payload.submesh]}s"] = len(
            values[index + 1]
        )
        row[f"{cmp_territory_name} - Nombre de {MESH_TITLES[payload.submesh]}s"] = len(
            cmp_values[index + 1]
        )
        row[f"{territory_name} - échantillon de dix territoires"] = " | ".join(
            values[index + 1][:10]
        )
        row[f"{cmp_territory_name} - échantillon de dix territoires"] = " | ".join(
            cmp_values[index + 1][:10]
        )
        rows.append(row)
    return export_to_csv(request, indicator, GraphType.comparison_histogram, rows)


def get_label(props, indicator, key):
    labels = {
        "annee": "Année",
        "lieu": "Lieu",
        "territory_1": "Origine",
        "territory_2": "Destination",
        "valeur": "flux" if props.flows else indicator.unite,
        "valeur_alternative": indicator.unite_alternative,
        "dimension": "Dimension",
    }
    for dimension in indicator.dimensions.all():
        labels[dimension.db_name] = dimension.title
    return labels[key]


def get_pages(count, limit, current):
    length = count // limit
    if count % limit != 0 or count == 0:
        length += 1
    page_range = list(range(1, length + 1))
    pages = {
        "first": page_range[0] if page_range[0] != current else None,
        "last": page_range[-1] if page_range[-1] != current else None,
        "current": current,
        "before": current - 1 if current - 1 in page_range else None,
        "after": current + 1 if current + 1 in page_range else None,
        "only_one_page": page_range == [1],
    }
    return pages


def get_line_focus(payload: IndicatorTablePayload):
    if not payload.focus:
        return None
    limit = payload.limit
    previous_limit = payload.previous_limit
    if limit and previous_limit:
        if limit <= previous_limit:
            return 1
        else:
            return previous_limit + 1
    return None


@require_GET
@use_payload(IndicatorTablePayload)
def indicator_details_table_view(request, name, payload):
    indicator = get_object_or_404(Indicator, name=name)
    filters = get_filters(request, indicator)
    count, data = get_count_and_data_for_indicator_table(indicator, payload, filters)
    formated_data = [format_data(element, precise=True) for element in data]
    keys = [
        {"db": key, "label": get_label(payload, indicator, key)}
        for key in (formated_data[0].keys() if formated_data else [])
    ]
    last_year = None
    if data and "annee" in data[0].keys():
        last_year = max([d["annee"] for d in data])
    context = {
        "rows": formated_data,
        "keys": keys,
        "result_count": count,
        "pages": get_pages(count, payload.limit, payload.pagination),
        "props": payload,
        "last_year": last_year,
        "line_focus": get_line_focus(payload),
    }
    return render(
        request,
        "territories_dashboard_lib/website/pages/indicators/details/components/table.html",
        context,
    )


@require_GET
@use_payload(IndicatorTablePayload)
def indicator_details_table_export_view(request, name, payload):
    indicator = get_object_or_404(Indicator, name=name)
    filters = get_filters(request, indicator)
    table_values = get_export_indicator_table_values(indicator, payload, filters)
    return export_to_csv(request, indicator, GraphType.table, table_values)
