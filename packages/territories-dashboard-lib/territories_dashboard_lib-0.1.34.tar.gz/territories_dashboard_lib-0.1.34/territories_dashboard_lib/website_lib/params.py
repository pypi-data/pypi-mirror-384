from functools import wraps

from territories_dashboard_lib.indicators_lib.enums import (
    FRANCE_GEOLEVEL_TITLES,
    MESH_TITLES,
    FranceGeoLevel,
    MeshLevel,
    get_all_meshes,
    get_allow_same_mesh,
)
from territories_dashboard_lib.indicators_lib.query.utils import run_custom_query

TERRITORY_DEFAULT = {
    "id": FranceGeoLevel.METRO,
    "mesh": MeshLevel.National,
    "name": FRANCE_GEOLEVEL_TITLES[FranceGeoLevel.METRO],
}

CMP_TERRITORY_DEFAULT = {
    "id": FranceGeoLevel.All,
    "mesh": MeshLevel.National,
    "name": FRANCE_GEOLEVEL_TITLES[FranceGeoLevel.All],
}

TERRITORY_PARAM_NAME = "territory"
CMP_TERRITORY_PARAM_NAME = "cmp-territory"
MESH_PARAM_NAME = "mesh"
ONE_WEEK_IN_SECONDS = 604800


class BadParam(Exception):
    pass


# TODO coverage
# appeler la page détail d'un indicateur (page html, pas api) avec plus de combinaisons de paramètres GET
# tester les valeurs du context du template
class ParamsHandler:
    def __init__(self, request):
        self.request = request
        self.territory_id = None
        self.territory_mesh = None
        self.territory_name = None
        self.cmp_territory_id = None
        self.cmp_territory_mesh = None
        self.cmp_territory_name = None
        self.mesh = None
        self.meshes = []
        self.comparison = request.resolver_match.view_name == "website:comparison"

    ######################## Territory

    def parse_territory(self, territory):
        if not territory:
            raise BadParam
        parts = territory.split("-")
        allowed_chars = set(
            "0123456789AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz, "
        )
        if (
            len(parts) != 2
            or not all(char in allowed_chars for char in parts[0])
            or parts[1] not in MeshLevel
        ):
            raise BadParam
        return parts[0], parts[1]

    def get_territory_name(self, territory_id, territory_mesh):
        if territory_mesh == MeshLevel.National:
            return FRANCE_GEOLEVEL_TITLES[territory_id]
        mesh = "DEPCOM" if territory_mesh == "com" else territory_mesh.upper()
        query = f"""
        SELECT DISTINCT "NOM_{mesh}" AS name FROM arborescence_geo
        WHERE "{mesh}" = '{territory_id}'
        """
        try:
            results = run_custom_query(query)
        except Exception:
            raise BadParam
        if not results:
            raise BadParam
        return results[0]["name"]

    def get_territory_default(self, cookie_territory):
        try:
            territory_id, territory_mesh = self.parse_territory(cookie_territory)
            territory_name = self.get_territory_name(territory_id, territory_mesh)
        except BadParam:
            return (
                TERRITORY_DEFAULT["id"],
                TERRITORY_DEFAULT["mesh"],
                TERRITORY_DEFAULT["name"],
            )
        return territory_id, territory_mesh, territory_name

    def choose_territory(self):
        url_territory = self.request.GET.get(TERRITORY_PARAM_NAME)
        try:
            territory_id, territory_mesh = self.parse_territory(url_territory)
            self.territory_name = self.get_territory_name(territory_id, territory_mesh)
            self.territory_id = territory_id
            self.territory_mesh = territory_mesh
        except BadParam:
            cookie_territory = self.request.COOKIES.get(TERRITORY_PARAM_NAME)
            self.territory_id, self.territory_mesh, self.territory_name = (
                self.get_territory_default(cookie_territory)
            )

    def construct_territory_value(self):
        return f"{self.territory_id}-{self.territory_mesh}"

    def territory_is_not_default(self):
        return (
            self.territory_id != TERRITORY_DEFAULT["id"]
            or self.territory_mesh != TERRITORY_DEFAULT["mesh"]
        )

    ######################## Compared Territory

    def choose_cmp_territory(self):
        url_territory = self.request.GET.get(CMP_TERRITORY_PARAM_NAME)
        try:
            territory_id, territory_mesh = self.parse_territory(url_territory)
            self.cmp_territory_name = self.get_territory_name(
                territory_id, territory_mesh
            )
            self.cmp_territory_id = territory_id
            self.cmp_territory_mesh = territory_mesh
        except BadParam:
            cookie_territory = self.request.COOKIES.get(CMP_TERRITORY_PARAM_NAME)
            self.cmp_territory_id, self.cmp_territory_mesh, self.cmp_territory_name = (
                self.get_territory_default(cookie_territory)
            )

    def construct_cmp_territory_value(self):
        return f"{self.cmp_territory_id}-{self.cmp_territory_mesh}"

    def cmp_territory_is_not_default(self):
        return (
            self.cmp_territory_id != CMP_TERRITORY_DEFAULT["id"]
            or self.cmp_territory_mesh != CMP_TERRITORY_DEFAULT["mesh"]
        )

    ######################## Mesh

    def get_max_territory_mesh(self):
        meshes = get_all_meshes()
        if self.comparison is False:
            return self.territory_mesh
        if meshes.index(self.cmp_territory_mesh) > meshes.index(self.territory_mesh):
            return self.cmp_territory_mesh
        return self.territory_mesh

    def is_not_valid_mesh(self, mesh):
        if mesh is None:
            return True
        meshes = get_all_meshes()
        max_territory_mesh = self.get_max_territory_mesh()
        allow_same_mesh = get_allow_same_mesh()
        is_not_valid = (
            meshes.index(max_territory_mesh) > meshes.index(mesh)
            if allow_same_mesh
            else meshes.index(max_territory_mesh) >= meshes.index(mesh)
        )
        return is_not_valid

    def get_default_mesh(self):
        max_territory_mesh = self.get_max_territory_mesh()
        meshes = get_all_meshes()
        if meshes.index(max_territory_mesh) == len(meshes) - 1:
            default_mesh = meshes[-1]
        else:
            mesh_index = meshes.index(max_territory_mesh)
            if get_allow_same_mesh() is False:
                mesh_index += 1
            default_mesh = meshes[mesh_index]
        return default_mesh

    def get_cookie_mesh(self):
        value = self.request.COOKIES.get(MESH_PARAM_NAME)
        if not value:
            return None
        parts = value.split("-")
        if len(parts) != 2 or parts[0] not in MeshLevel or parts[1] not in MeshLevel:
            return None
        if self.territory_mesh != parts[0]:
            return None
        return parts[1]

    def choose_mesh(self):
        url_mesh = self.request.GET.get(MESH_PARAM_NAME)
        url_mesh = url_mesh if url_mesh in MeshLevel else None
        if self.is_not_valid_mesh(url_mesh):
            cookie_mesh = self.get_cookie_mesh()
            if self.is_not_valid_mesh(cookie_mesh):
                self.mesh = self.get_default_mesh()
            else:
                self.mesh = cookie_mesh
        else:
            self.mesh = url_mesh
        max_territory_mesh = self.get_max_territory_mesh()
        meshes = [
            m
            for m in get_all_meshes()
            if not (m == MeshLevel.Town and max_territory_mesh == MeshLevel.National)
        ]
        min_mesh_index = meshes.index(max_territory_mesh)
        if get_allow_same_mesh() is False:
            min_mesh_index += 1
        self.meshes = meshes[min(min_mesh_index, len(meshes) - 1) :]

    ######################## Commons

    def set_cookie(self, response):
        if self.territory_is_not_default():
            response.set_cookie(
                key=TERRITORY_PARAM_NAME,
                value=self.construct_territory_value(),
                max_age=ONE_WEEK_IN_SECONDS,
            )
        else:
            response.delete_cookie(TERRITORY_PARAM_NAME)
        if self.cmp_territory_is_not_default():
            response.set_cookie(
                key=CMP_TERRITORY_PARAM_NAME,
                value=self.construct_cmp_territory_value(),
                max_age=ONE_WEEK_IN_SECONDS,
            )
        else:
            response.delete_cookie(CMP_TERRITORY_PARAM_NAME)
        if self.mesh != self.get_default_mesh():
            response.set_cookie(
                key=MESH_PARAM_NAME,
                value=f"{self.territory_mesh}-{self.mesh}",
                max_age=ONE_WEEK_IN_SECONDS,
            )
        else:
            response.delete_cookie(MESH_PARAM_NAME)

    def add_to_context(self, context):
        url_params = []
        if self.territory_is_not_default():
            url_params.append(
                f"{TERRITORY_PARAM_NAME}={self.construct_territory_value()}"
            )
        if self.comparison and self.cmp_territory_is_not_default():
            url_params.append(
                f"{CMP_TERRITORY_PARAM_NAME}={self.construct_cmp_territory_value()}"
            )
        if self.mesh != self.get_default_mesh():
            url_params.append(f"{MESH_PARAM_NAME}={self.mesh}")
        context["params"] = {
            "territory_id": self.territory_id,
            "territory_mesh": self.territory_mesh,
            "territory_name": self.territory_name,
            "cmp_territory_id": self.cmp_territory_id,
            "cmp_territory_mesh": self.cmp_territory_mesh,
            "cmp_territory_name": self.cmp_territory_name,
            "mesh": self.mesh,
            "meshes": self.meshes,
            "meshes_titles": MESH_TITLES,
            "all_meshes": get_all_meshes(),
            "url_params": "&".join(url_params),
        }


def with_params(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        handler = ParamsHandler(request)
        handler.choose_territory()
        handler.choose_cmp_territory()
        handler.choose_mesh()

        context = kwargs.get("context", {})
        handler.add_to_context(context)

        response = view_func(request, *args, context=context, **kwargs)
        handler.set_cookie(response)
        return response

    return wrapper
