from django.conf import settings
from django.db import models


class AggregationFunctions(models.TextChoices):
    DISCRETE_COMPONENT_2 = "discrete"
    REPEATED_COMPONENT_2 = "repeated"


class MeshLevel(models.TextChoices):
    National = "fr"
    Region = "reg"
    Department = "dep"
    Epci = "epci"
    Town = "com"


class GeoLevel(models.TextChoices):
    France = "fr"
    Region = "reg"
    Department = "dep"
    Epci = "epci"
    Town = "com"


class FranceGeoLevel(models.TextChoices):
    All = "FR0,FR1,FR2"
    METRO = "FR0,FR1"
    METRO_HORS_IDF = "FR0"


FRANCE_GEOLEVEL_TITLES = {
    FranceGeoLevel.All: "France entière",
    FranceGeoLevel.METRO: "France métropolitaine",
    FranceGeoLevel.METRO_HORS_IDF: "France métropolitaine hors IDF",
}

FRANCE_DB_VALUES = {
    FranceGeoLevel.All: "FR_TOT",
    FranceGeoLevel.METRO: "FR_METRO",
    FranceGeoLevel.METRO_HORS_IDF: "FR_METRO_HORS_IDF",
}


DEFAULT_MESH = MeshLevel.Region

MESH_TITLES = {
    MeshLevel.National: "France entière",
    MeshLevel.Region: "Région",
    MeshLevel.Department: "Département",
    MeshLevel.Epci: "Intercommunalité",
    MeshLevel.Town: "Commune",
}

MESH_DB = {
    MeshLevel.Region: "REG",
    MeshLevel.Department: "DEP",
    MeshLevel.Epci: "EPCI",
    MeshLevel.Town: "DEPCOM",
}


def get_miminum_mesh():
    try:
        town_mesh_is_disabled = settings.DISABLE_TOWN_MESH
        return MeshLevel.Epci if town_mesh_is_disabled else MeshLevel.Town
    except AttributeError:
        return MeshLevel.Town


def get_allow_same_mesh():
    try:
        return bool(settings.ALLOW_SAME_MESH)
    except AttributeError:
        return False


def get_all_meshes():
    min_mesh = get_miminum_mesh()
    meshes = []
    for m in MeshLevel:
        meshes.append(m)
        if m == min_mesh:
            break
    return meshes
