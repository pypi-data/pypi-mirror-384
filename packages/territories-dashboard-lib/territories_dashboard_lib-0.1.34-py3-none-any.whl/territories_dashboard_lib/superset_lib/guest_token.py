import http.client
import json

from django.conf import settings


def get_guest_token(dashboard_id):
    """
    Function copied from https://snum.gitlab-pages.din.developpement-durable.gouv.fr/ds/gd3ia/offre-dataviz-documentation/05-Documentation_SUPERSET_INTEGRATION/
    """
    conn = http.client.HTTPSConnection(settings.SUPERSET_DOMAIN)
    params = json.dumps(
        {
            "provider": "db",
            "refresh": "True",
            "username": settings.SUPERSET_USERNAME,
            "password": settings.SUPERSET_PASSWORD,
        }
    )
    conn.request(
        "POST", "/api/v1/security/login", params, {"Content-Type": "application/json"}
    )
    response = conn.getresponse()
    content = json.loads(response.read())
    access_token = content["access_token"]

    # Recuperation du token CSRF et cookie de session associe
    headers = {"Authorization": f"Bearer {access_token}"}
    conn.request("GET", "/api/v1/security/csrf_token/", None, headers)
    response = conn.getresponse()
    content = json.loads(response.read())
    csrf_token = content["result"]
    cookie = response.headers["set-cookie"].split("; ")[0]

    # Recuperation du guest_token pour l'affichage du diagramme
    params = json.dumps(
        {
            "resources": [{"id": dashboard_id, "type": "dashboard"}],
            "rls": [
                {
                    # Clause SQL appliquée à la récupération des donnes du dashboard
                    # Elle peut être ajustée pour limiter les données affichées
                    # dans le dashboard en fonction du profil utilisateur
                    # La valeur "1=1" permet de n'appliquer aucun filtre
                    "clause": "1=1"
                }
            ],
            "user": {
                "first_name": "Prenom",
                "last_name": "Nom",
                "username": settings.SUPERSET_USERNAME,
            },
        }
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "X-Csrftoken": csrf_token,
        "Cookie": cookie,
    }
    conn.request("POST", "/api/v1/security/guest_token/", params, headers)
    response = conn.getresponse()
    guest_token = json.loads(response.read())["token"]
    return guest_token
