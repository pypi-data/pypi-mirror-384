import base64
import datetime
import gzip
import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from psycopg2.sql import SQL, Identifier, Literal

from territories_dashboard_lib.geo_lib.payloads import (
    GeoFeaturesParams,
    MainTerritoryParams,
    SearchTerritoriesParams,
    TerritoriesParams,
    TerritoryFeatureParams,
)
from territories_dashboard_lib.indicators_lib.enums import (
    FRANCE_GEOLEVEL_TITLES,
    MESH_DB,
    MeshLevel,
)
from territories_dashboard_lib.indicators_lib.query.commons import get_territories_ids
from territories_dashboard_lib.indicators_lib.query.utils import run_custom_query

from .enums import GeoFeatureType
from .models import GeoFeature


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return (
                obj.date().isoformat()
                if isinstance(obj, datetime.datetime)
                else obj.isoformat()
            )
        return super().default(obj)


@require_GET
@cache_control(max_age=3600)
def geo_features_view(request):
    params = GeoFeaturesParams(**request.GET.dict())

    geo_feature = get_object_or_404(GeoFeature, id=params.feature)
    geo_level = params.geo_level
    mesh = params.mesh
    main_territory_codes = params.main_territories
    last = params.last
    limit = params.limit

    last_year_query = (
        f"SELECT DISTINCT annee FROM {geo_feature.name} ORDER BY annee DESC"
    )
    years = run_custom_query(last_year_query)
    last_year = years[0].get("annee")

    territories_ids = get_territories_ids(main_territory_codes, geo_level, mesh)

    col_id_name = f"code_{mesh}"
    columns = [el.name for el in geo_feature.items.all()]

    coma = ", " if columns else ""
    select_geo_code = (
        f", geo.{col_id_name} AS geo_code"
        if geo_feature.geo_type == GeoFeatureType.point
        else ""
    )

    if geo_feature.geo_type == GeoFeatureType.point:
        where_clause = f"WHERE geo.{col_id_name} IN ('{"', '".join(territories_ids)}')"
    else:
        where_clause = (
            f"JOIN contours_simplified_{geo_level} contours ON ST_intersects(geo.geometry, contours.geometry)\n"
            f"WHERE contours.code IN ('{"', '".join(main_territory_codes)}')"
        )
    where_clause += f" AND annee = {last_year}"

    pagination = f"AND order_id > {last or 0} ORDER BY order_id ASC LIMIT {limit}"

    query = (
        f"SELECT ST_asgeojson(geo.geometry) AS geojson, order_id{coma + ', '.join(columns)}\n"
        f"{select_geo_code}\n"
        f"FROM {geo_feature.name} AS geo\n"
        f"{where_clause} {pagination}"
    )

    # Execute the query
    results = run_custom_query(query)

    items = geo_feature.items.all()
    # Transform results
    data = [
        {
            "type": "Feature",
            "id": r.get("geo_code"),
            "properties": {el.label: r.get(el.name) for el in items},
            "geometry": json.loads(r.get("geojson")),
        }
        for r in results
    ]

    last_queried_order_id = results[-1]["order_id"] if results else None

    compressed_data = gzip.compress(json.dumps(data, cls=DateTimeEncoder).encode())
    compressed_base64 = base64.b64encode(compressed_data).decode()

    return JsonResponse({"data": compressed_base64, "last": last_queried_order_id})


@require_GET
@cache_control(max_age=3600)
def main_territory_view(request):
    params = MainTerritoryParams(**request.GET.dict())

    codes = ", ".join(f"'{code.strip()}'" for code in params.geo_id)

    query = f"""
        SELECT code as id, ST_asgeojson(ST_simplify(geometry, 0.01)) AS polygon
        FROM contours_simplified_{params.geo_level}
        WHERE code IN ({codes})
        """

    results = run_custom_query(query)

    data = [
        {
            "id": r.get("id"),
            "polygon": json.loads(r.get("polygon")),
        }
        for r in results
    ]

    return JsonResponse(data, safe=False)


@require_GET
@cache_control(max_age=3600)
def precise_view(request):
    params = TerritoriesParams(**request.GET.dict())
    mesh_level = params.mesh
    territories_ids = params.territories

    if not mesh_level:
        return JsonResponse({"error": "Missing 'mesh' parameter"}, status=400)

    mapped_mesh_level = "DEPCOM" if mesh_level == "com" else mesh_level.upper()

    query = f"""
        SELECT "{mapped_mesh_level}" AS id, ST_asgeojson(geometry) AS polygon
        FROM contours_geo_ign_{mesh_level}
        WHERE "{mapped_mesh_level}" IN ('{"', '".join(territories_ids)}')
        """

    results = run_custom_query(query)

    territories = {r.get("id"): json.loads(r.get("polygon")) for r in results}

    return JsonResponse(territories)


@require_GET
@cache_control(max_age=3600)
def territories_view(request):
    params = TerritoryFeatureParams(**request.GET.dict())
    geo_level = params.geo_level
    mesh = params.mesh

    if params.codes:
        territories_ids = params.codes
    else:
        main_territory_codes = params.main_territories
        territories_ids = get_territories_ids(main_territory_codes, geo_level, mesh)

    query = f"""
        SELECT code AS id, ST_asgeojson(geometry) AS polygon
        FROM contours_simplified_{params.mesh}
        WHERE code IN ('{"', '".join(territories_ids)}')
        """

    results = run_custom_query(query)

    data = [
        {"type": "Feature", "id": r.get("id"), "geometry": json.loads(r.get("polygon"))}
        for r in results
    ]
    return JsonResponse(data, safe=False)


def _fill_territory_li(code, name, mesh):
    label = name if mesh == MeshLevel.National else f"{name} - {code}"
    return f"""<li data-code="{code}" data-name="{name}" onclick="chooseTerritory(this)"><button aria-label="Choisir {label}">{label}</button></li>"""


@require_GET
@cache_control(max_age=3600)
def search_territories_view(request):
    params = SearchTerritoriesParams(**request.GET.dict())
    mesh = params.mesh
    search = params.search
    offset = params.offset
    if mesh == MeshLevel.National:
        lis = []
        for code, name in FRANCE_GEOLEVEL_TITLES.items():
            li = _fill_territory_li(code, name, mesh)
            lis.append(li)
        return HttpResponse("\n".join(lis))
    mesh_db = MESH_DB[mesh]
    pagination = 20
    query = SQL("""
    SELECT DISTINCT {code} as code, {name} as name FROM arborescence_geo
    WHERE unaccent({name}) || {code} ILIKE unaccent(%s)
    AND "FR" <> 'ETR'
    ORDER BY {name}, {code}
    LIMIT {limit} OFFSET {offset};
    ;
    """).format(
        code=Identifier(mesh_db),
        name=Identifier(f"NOM_{mesh_db}"),
        offset=Literal(offset * pagination),
        limit=Literal(pagination),
    )
    territories = run_custom_query(query, [f"%{search}%"])
    lis = []
    for territory in territories:
        li = _fill_territory_li(territory["code"], territory["name"], mesh)
        lis.append(li)
    if len(territories) == pagination:
        li = f"""<li data-type="load"><button onclick="loadMoreTerritories(this)" data-mesh="{mesh}" data-offset="{offset + 1}" class="fr-btn fr-btn--secondary fr-btn--sm">Charger plus de résultats</button></li>"""
        lis.append(li)
    return HttpResponse("\n".join(lis))
