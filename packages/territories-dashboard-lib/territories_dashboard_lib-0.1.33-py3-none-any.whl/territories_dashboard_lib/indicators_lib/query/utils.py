from django.conf import settings
from django.db import connections


def get_breakdown_dimension(indicator):
    breakdown_dimension = (
        indicator.dimensions.filter(is_breakdown=True).first()
        if indicator.dimensions.count() > 1
        else indicator.dimensions.first()
    )
    return breakdown_dimension


def get_connection():
    """
    The connection to the indicators database is defined in DATABASES
    The key for the database in DATABASES is defined in settings.INDICATORS_DATABASE
    During testing, the connection can also be defined in READONLY_DATABASES_HANDLER
    which defines a readonly database which will not be recreated during tests
    """
    connection = None
    indicators_database = getattr(settings, "INDICATORS_DATABASE", None)
    if indicators_database:
        connection = connections[indicators_database]
    else:
        testing = getattr(settings, "TESTING", False)
        readonly_databases_handler = getattr(
            settings, "READONLY_DATABASES_HANDLER", None
        )
        if testing and readonly_databases_handler:
            connection = readonly_databases_handler["default"]
    if connection is None:
        raise ValueError("No connection was defined for the indicators database")
    return connection


def run_custom_query(query, params=None):
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        results = [dict(zip(columns, row)) for row in rows]
        return results
