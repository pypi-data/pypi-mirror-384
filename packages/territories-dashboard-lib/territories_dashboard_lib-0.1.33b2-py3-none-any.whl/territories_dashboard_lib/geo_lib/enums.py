from django.db import models


class GeoFeatureType(models.TextChoices):
    point = "point"
    line = "line"
    polygon = "polygon"
