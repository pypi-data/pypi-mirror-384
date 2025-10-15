from django import template
from django.urls import reverse
from territories_dashboard_lib.indicators_lib.enums import get_all_meshes

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def indicator_api_urls(indicator_dict):
    view_names = [
        "download-indicator-methodo",
        "statistics",
        "values",
        "histogram",
        "top-10",
        "details-table",
        "details-table-export",
        "comparison-histogram",
        "proportions",
    ]
    return {
        view_name: reverse(
            f"indicators-api:{view_name}", kwargs={"name": indicator_dict["name"]}
        )
        for view_name in view_names
    }


@register.filter
def should_mesh_analysis(params, indicator):
    meshes = get_all_meshes()
    above_min_mesh = meshes.index(params["mesh"]) <= meshes.index(indicator["min_mesh"])
    return above_min_mesh
