from django.urls import path

from .views import (
    comparison_histogram_export_view,
    comparison_histogram_view,
    download_indicator_methodo_view,
    flows_view,
    indicator_details_table_export_view,
    indicator_details_table_view,
    indicator_histogram_export_view,
    indicator_histogram_view,
    indicator_proportions_export_view,
    indicator_statistics_view,
    indicator_submesh_territories_view,
    indicator_top_10_export_view,
    indicator_top_10_view,
    indicator_values_export_view,
    indicator_values_view,
    proportions_chart_view,
)

app_name = "indicators-api"

urlpatterns = [
    path("flows/", flows_view, name="flows"),
    path(
        "<str:name>/methodo/",
        download_indicator_methodo_view,
        name="download-indicator-methodo",
    ),
    path(
        "<str:name>/statistics/",
        indicator_statistics_view,
        name="statistics",
    ),
    path(
        "<str:name>/values/export/",
        indicator_values_export_view,
        name="values-export",
    ),
    path(
        "<str:name>/values/",
        indicator_values_view,
        name="values",
    ),
    path(
        "<str:name>/histogram/export/",
        indicator_histogram_export_view,
        name="histogram-export",
    ),
    path(
        "<str:name>/histogram/",
        indicator_histogram_view,
        name="histogram",
    ),
    path(
        "<str:name>/top-10/export/",
        indicator_top_10_export_view,
        name="top-10-export",
    ),
    path(
        "<str:name>/top-10/",
        indicator_top_10_view,
        name="top-10",
    ),
    path(
        "<str:name>/details/table/",
        indicator_details_table_view,
        name="details-table",
    ),
    path(
        "<str:name>/details/table/export/",
        indicator_details_table_export_view,
        name="details-table-export",
    ),
    path(
        "<str:name>/comparison-histogram/export/",
        comparison_histogram_export_view,
        name="comparison-histogram-export",
    ),
    path(
        "<str:name>/comparison-histogram/",
        comparison_histogram_view,
        name="comparison-histogram",
    ),
    path(
        "<str:name>/proportions/export/",
        indicator_proportions_export_view,
        name="proportions-export",
    ),
    path(
        "<str:name>/proportions/",
        proportions_chart_view,
        name="proportions",
    ),
    path("<str:name>/submesh/", indicator_submesh_territories_view, name="submesh"),
]
