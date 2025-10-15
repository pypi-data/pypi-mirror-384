from django.db import models
from django.utils import timezone

from territories_dashboard_lib.indicators_lib.enums import MeshLevel
from territories_dashboard_lib.tracking_lib.enums import EventType


class Page(models.Model):
    """
    Une vue correspond à l'ouverture d'une des pages de l'application.
    À chaque changement de paramètre (territoire, maille, territoire de comparaison) une nouvelle vue est enregistrée.
    """

    created_at = models.DateTimeField(default=timezone.now)
    cookie = models.TextField(
        help_text="Un cookie sans durée d'expiration est placé dans chaque nouvelle session, il possède une valeur aléatoire qui permet de tracer le navigateur du visiteur entre plusieurs visites."
    )
    territory_id = models.TextField(
        help_text="ID du territoire principal sélectionné.", null=True, blank=True
    )
    territory_mesh = models.TextField(
        choices=MeshLevel.choices,
        help_text="Maille du territoire principal sélectionné.",
        null=True,
        blank=True,
    )
    submesh = models.TextField(
        choices=MeshLevel.choices,
        help_text="Maille d'analyse sélectionnée.",
        null=True,
        blank=True,
    )
    cmp_territory_id = models.TextField(
        null=True,
        blank=True,
        help_text="ID du territoire de comparaison, null s'il ne s'agit pas de la page comparaison.",
    )
    cmp_territory_mesh = models.TextField(
        choices=MeshLevel.choices,
        null=True,
        blank=True,
        help_text="Maille du territoire de comparaison, null s'il ne s'agit pas de la page comparaison.",
    )
    indicator = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID de l'indicateur de la page détails, null s'il ne s'agit pas de la page détails, utile pour faire des jointures.",
    )
    indicator_name = models.TextField(
        null=True,
        blank=True,
        help_text="Nom de l'indicateur de la page détails, null s'il ne s'agit pas de la page détails, utile pour une analyse rapide.",
    )
    theme = models.IntegerField(
        help_text="ID du thème de la page, utile pour faire des jointures.",
        null=True,
        blank=True,
    )
    theme_name = models.TextField(
        help_text="Nom du thème de la page, utile pour une analyse rapide.",
        null=True,
        blank=True,
    )
    url = models.TextField(help_text="URL brut de la page")
    view = models.TextField(help_text="Nom de la vue dans Django")


class Event(models.Model):
    """
    Tracking des autres événements de l'application
    """

    created_at = models.DateTimeField(default=timezone.now)
    cookie = models.TextField(
        help_text="Un cookie sans durée d'expiration est placé dans chaque nouvelle session, il possède une valeur aléatoire qui permet de tracer le navigateur du visiteur entre plusieurs visites."
    )
    name = models.TextField(choices=EventType.choices)
    data = models.JSONField(null=True, blank=True)
    url = models.TextField(help_text="URL brut de la page")
    view = models.TextField(help_text="Nom de la vue dans Django")


class CookieInfo(models.Model):
    id = models.TextField(primary_key=True)
    country = models.TextField(null=True, blank=True)
    ip_address = models.TextField(null=True, blank=True)
