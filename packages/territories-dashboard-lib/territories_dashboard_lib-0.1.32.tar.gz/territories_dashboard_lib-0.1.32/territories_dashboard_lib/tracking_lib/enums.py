from django.db import models

TRACKING_COOKIE_NAME = "omnibus"


class EventType(models.TextChoices):
    download = "download"


class GraphType(models.TextChoices):
    comparaison_historique = "comparaison-historique"
    repartition_dimension = "repartition-dimension"
    repartition_valeurs = "repartition-valeurs"
    top_10 = "top_10"
    historique = "historique"
    comparison_histogram = "comparison-histogram"
    table = "table"
