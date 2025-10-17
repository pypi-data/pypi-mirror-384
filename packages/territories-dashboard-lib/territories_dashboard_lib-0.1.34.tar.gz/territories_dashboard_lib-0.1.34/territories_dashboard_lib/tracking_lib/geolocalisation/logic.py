import os
from functools import lru_cache

import geoip2.database


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


@lru_cache(maxsize=100_000)
def get_country_from_geolite(ip_address):
    database_name = "GeoLite2-Country.mmdb"
    database_path = os.path.join(os.path.dirname(__file__), database_name)
    reader = geoip2.database.Reader(database_path)
    try:
        response = reader.country(ip_address)
        country = response.country.iso_code
    except geoip2.errors.AddressNotFoundError:
        country = "UNKNOWN"
    reader.close()
    return country
