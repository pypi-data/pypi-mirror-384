from django.db import models
from martor.models import MartorField

from territories_dashboard_lib.commons.models import CommonModel
from territories_dashboard_lib.indicators_lib.enums import (
    AggregationFunctions,
    MeshLevel,
)
from territories_dashboard_lib.indicators_lib.refresh_filters import refresh_filters


class Theme(CommonModel):
    # TODO: make it primary key
    # django.db.utils.OperationalError: foreign key mismatch -
    # "tdbmd_indicators_indicatorsubtheme" referencing "tdbmd_indicators_indicatortheme"
    ordering = models.IntegerField(default=0)
    ordering.verbose_name = "Ordre dans la sidebar"
    name = models.CharField(max_length=64, unique=True)
    name.verbose_name = "Nom (~id, URL)"
    title = models.CharField(max_length=128)
    title.verbose_name = "Titre (affiché)"
    objectif_theme = models.TextField(blank=True)
    objectif_theme.verbose_name = "Objectif"
    action_theme = models.TextField(blank=True)
    action_theme.verbose_name = "Actions"

    def is_displayed_on_app(self):
        return self.sub_themes.all().exists()

    is_displayed_on_app.__name__ = "Visible ?"
    is_displayed_on_app.boolean = True

    def subthemes_count(self):
        return self.sub_themes.count()

    subthemes_count.__name__ = "Nb sous-thèmes"

    def indicators_count(self):
        return sum(
            [sub_theme.indicators_count() for sub_theme in self.sub_themes.all()]
        )

    indicators_count.__name__ = "Total indicateurs"

    def __str__(self):
        return self.title

    class Meta:
        ordering = ("ordering",)
        verbose_name = "1 - Thème"
        indexes = [
            models.Index(fields=["name"]),
        ]


class SubTheme(CommonModel):
    name = models.CharField(max_length=64, unique=True)
    name.verbose_name = "Nom (~id, URL)"
    theme = models.ForeignKey(
        Theme, on_delete=models.CASCADE, related_name="sub_themes"
    )
    theme.verbose_name = "Thème"
    index_in_theme = models.IntegerField(default=0)
    index_in_theme.verbose_name = "Ordre thème"
    title = models.CharField(max_length=128)
    title.verbose_name = "Titre (affiché)"
    description = models.TextField(default="", blank=True)

    def __str__(self):
        return f"{self.theme.title} > {self.title}"

    def indicators_count(self):
        return self.indicators.count()

    def is_displayed_on_app(self):
        return self.indicators.all().exists()

    indicators_count.__name__ = "Nb indicateurs"
    is_displayed_on_app.__name__ = "Visible ?"
    is_displayed_on_app.boolean = True

    class Meta:
        ordering = ("theme", "index_in_theme")
        verbose_name = "2 - Sous-thème"
        indexes = [
            models.Index(fields=["theme", "index_in_theme"]),
            models.Index(fields=["name"]),
        ]


class Indicator(CommonModel):
    is_active = models.BooleanField(default=True)
    is_active.verbose_name = "Actif ?"
    sub_theme = models.ForeignKey(
        SubTheme, on_delete=models.CASCADE, related_name="indicators"
    )
    sub_theme.verbose_name = "Sous-thème"
    index_in_theme = models.IntegerField(default=0)  # TODO: is it necessary?
    index_in_theme.verbose_name = "Ordre sous-thème"
    name = models.CharField(max_length=32, unique=True)
    name.verbose_name = "Nom (~id, URL)"
    title = models.CharField(max_length=128)
    title.verbose_name = "Titre (affiché)"
    short_title = models.CharField(max_length=128, null=True, blank=True)
    short_title.verbose_name = "Titre abrégé"
    # Indicator's DB attributes
    db_table_prefix = models.CharField(max_length=128)
    db_table_prefix.verbose_name = "Préfixe dans la DB"
    min_mesh = models.TextField(choices=MeshLevel.choices, default=MeshLevel.Town)
    is_composite = models.BooleanField(default=False)
    is_composite.verbose_name = "Indicateur composite"
    show_alternative = models.BooleanField(
        default=True,
        verbose_name="Afficher la valeur alternative",
        help_text="Pour certains indicateurs composites (par exemple les moyennes) on ne veut pas afficher la valeur alternative.",
    )
    aggregation_constant = models.DecimalField(
        default=1, decimal_places=5, max_digits=10
    )
    aggregation_constant.verbose_name = "Constante d'agrégation"
    aggregation_function = models.CharField(
        default=AggregationFunctions.REPEATED_COMPONENT_2,
        max_length=8,
        choices=AggregationFunctions.choices,
    )
    aggregation_function.verbose_name = "Fonction d'agrégation"
    unite = models.CharField(max_length=32)
    unite.verbose_name = "Unité (affichée)"
    unite_nom_accessible = models.CharField(
        max_length=64,
        default="",
        blank=True,
        help_text="Nom accessible de l'unité qui sera lu par le lecteur d'écran.",
    )
    unite_alternative = models.CharField(
        default=None, null=True, blank=True, max_length=32
    )
    unite_alternative.verbose_name = "Unité alternative (affichée)"
    unite_alternative_nom_accessible = models.CharField(
        max_length=64,
        default="",
        blank=True,
        help_text="Nom accessible de l'unité alternative qui sera lu par le lecteur d'écran.",
    )
    secondary_indicator = models.ForeignKey(
        "indicators_lib.Indicator",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Second indicateur à afficher sur la carte",
    )
    flows_db_table_prefix = models.CharField(
        null=True,
        blank=True,
        max_length=128,
        verbose_name="Table des flux (prefix)",
        help_text="Les données des flux seront affichés sur la carte et le graphique de Sankey.",
    )
    flows_dimension = models.CharField(
        null=True,
        blank=True,
        max_length=32,
        verbose_name="Dimension des flux",
        help_text="Nom de la colonne des dimensions de la table des flux",
    )
    # Descriptive attributes
    show_evolution = models.BooleanField(default=True)
    show_evolution.verbose_name = "Activer l'historique"
    source = models.TextField(default="", blank=True)
    description = models.TextField(default="", blank=True)
    methodo = MartorField(default="", blank=True)
    methodo.verbose_name = "Méthodologie (markdown)"
    methodo_file = models.BinaryField(null=True, blank=True)

    def __str__(self):
        return self.title

    def get_theme_title(self):
        return self.sub_theme.theme.title

    get_theme_title.short_description = "Thème"

    class Meta:
        ordering = ("sub_theme", "index_in_theme")
        verbose_name = "3 - Indicateur"
        indexes = [
            models.Index(fields=["sub_theme"]),
            models.Index(fields=["name"]),
        ]


class Dimension(CommonModel):
    indicator = models.ForeignKey(
        Indicator, on_delete=models.CASCADE, related_name="dimensions"
    )
    db_name = models.TextField()
    title = models.TextField()
    is_breakdown = models.BooleanField(
        default=False,
        verbose_name="Répartir selon cette dimension",
        help_text="Dans le cas de plusieurs dimensions pour un indicateur, l'une d'entre elles doit être la dimension de réparition pour les graphiques.",
    )

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        result = super().save(*args, **kwargs)
        if is_new:
            try:
                refresh_filters(self)
            except Exception as e:
                print(e)
        return result


class Filter(CommonModel):
    dimension = models.ForeignKey(
        Dimension, related_name="filters", on_delete=models.CASCADE
    )
    db_name = models.CharField(max_length=128)
    db_name.verbose_name = "Nom dans la BDD"
    order = models.IntegerField(default=0)
    order.verbose_name = "Ordre"
    default = models.BooleanField(default=True)
    default.verbose_name = "Sélectionné par défaut ?"
    color = models.TextField(
        null=True,
        blank=True,
        verbose_name="Couleur",
        help_text="format hexadécimale : #FF11DD",
    )

    def __str__(self):
        return self.db_name

    class Meta:
        ordering = ("dimension", "order", "db_name")
        verbose_name = "Filtre"
        indexes = [
            models.Index(fields=["db_name"]),
            models.Index(fields=["dimension", "order"]),
        ]
        unique_together = ("dimension", "db_name")
