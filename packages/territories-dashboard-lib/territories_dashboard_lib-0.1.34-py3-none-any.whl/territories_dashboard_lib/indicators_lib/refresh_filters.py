from django.apps import apps

from territories_dashboard_lib.indicators_lib.query.utils import run_custom_query


def refresh_filters(dimension):
    if dimension:
        query = f'SELECT DISTINCT({dimension.db_name}) as filter FROM "{dimension.indicator.db_table_prefix}_reg"'
        results = run_custom_query(query)
        Filter = apps.get_model("indicators_lib", "Filter")
        Filter.objects.filter(dimension=dimension).delete()
        Filter.objects.bulk_create(
            [
                Filter(dimension=dimension, db_name=value["filter"], order=index)
                for index, value in enumerate(results)
            ]
        )
