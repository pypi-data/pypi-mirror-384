from territories_dashboard_lib.indicators_lib.enums import MeshLevel
from territories_dashboard_lib.indicators_lib.query.utils import run_custom_query

from .models import Dashboard


def get_territory_meshes(territory_id: str, territory_mesh: MeshLevel):
    current_reg = None
    current_dep = None
    current_epci = None
    current_com = None
    if territory_mesh != MeshLevel.National:
        mapped_mesh = "DEPCOM" if territory_mesh == "com" else territory_mesh.upper()
        query = f"""
        SELECT
            "NOM_REG" as reg_name,
            "NOM_DEP" as dep_name,
            "NOM_EPCI" as epci_name,
            "NOM_DEPCOM" as com_name
        FROM arborescence_geo
        WHERE "{mapped_mesh}" = '{territory_id}'
        LIMIT 1
        """
        row = run_custom_query(query)[0]
        if territory_mesh in [
            MeshLevel.Region,
            MeshLevel.Department,
            MeshLevel.Epci,
            MeshLevel.Town,
        ]:
            current_reg = row["reg_name"]
        if territory_mesh in [
            MeshLevel.Department,
            MeshLevel.Epci,
            MeshLevel.Town,
        ]:
            current_dep = row["dep_name"]
        if territory_mesh in [
            MeshLevel.Epci,
            MeshLevel.Town,
        ]:
            current_epci = row["epci_name"]
        if territory_mesh in [
            MeshLevel.Town,
        ]:
            current_com = row["com_name"]
    territory_meshes = {
        MeshLevel.Region: current_reg,
        MeshLevel.Department: current_dep,
        MeshLevel.Epci: current_epci,
        MeshLevel.Town: current_com,
    }
    return territory_meshes


def make_filter(dashboard: Dashboard, territory_id: str, territory_mesh: MeshLevel):
    if dashboard.filters.count() == 0:
        return None
    territory_meshes = get_territory_meshes(territory_id, territory_mesh)
    filters = []
    for f in dashboard.filters.all():
        value = territory_meshes.get(f.mesh)
        if value:
            value = value.replace("'", "!'")  # RISON escape
            filter_string = f"""NATIVE_FILTER-{f.superset_id}:(__cache:(label:'{value}',validateStatus:!f,value:!('{value}')),extraFormData:(filters:!((col:{f.superset_col},op:IN,val:!('{value}')))),filterState:(label:'{value}',validateStatus:!f,value:!('{value}')),id:NATIVE_FILTER-{f.superset_id},ownState:())"""
            filters.append(filter_string)
    if not filters:
        return None
    return f"""({",".join(filters)})"""
