from django.db import models

from territories_dashboard_lib.commons.models import CommonModel
from territories_dashboard_lib.indicators_lib.enums import MeshLevel


class Dashboard(CommonModel):
    superset_id = models.TextField(
        unique=True,
        verbose_name="Embed ID de Superset",
        help_text="Un utilisateur administrateur de l'instance Superset doit accéder aux paramètres du dashboard et cliquer sur 'embed dashboard' pour récupérer cet ID nécessaire à la connexion avec l'instance Superset.",
    )
    short_name = models.TextField(
        unique=True,
        verbose_name="Nom court",
        help_text="Pour l'URL, ne mettre que des lettres minuscules sans accents et des tirets",
    )
    label = models.TextField(
        unique=True,
        verbose_name="Label",
        help_text="Nom du dashboard à afficher dans la liste.",
    )
    order = models.IntegerField(
        default=1,
        verbose_name="Numéro d'ordre",
        help_text="Numéro d'ordre dans la dropdown de sélection, les dashboards sont triés du plus petit numéro au plus grand.",
    )

    def __str__(self):
        return self.label


class Filter(CommonModel):
    dashboard = models.ForeignKey(
        Dashboard, on_delete=models.CASCADE, related_name="filters"
    )
    superset_id = models.TextField(
        null=True,
        blank=True,
        help_text="ID du native filter du territoire, qui permettra d'initialiser les filtres du dasbhoard au territoire sélectionné dans l'application. Pour le récupérer c'est un petit parcours du combattant : aller sur le dashboard dans superset, cliquer sur modifier le dashboard, cliquer sur les trois petits points, puis sur modifier les propriétés. Cliquer sur avancé, copier le json et le coller dans un site comme : https://jsonformatter.curiousconcept.com/ pour mieux le voir. Chercher 'global_chart_configuration' puis 'native_filter_configuration'. Chercher le native filter lié au choix du territoire. Copier l'id qui dans son nom, le nom est de la forme NATIVE_FILTER-ID. Promis, c'est le plus simple que j'ai trouvé !",
    )
    superset_col = models.TextField(
        null=True,
        blank=True,
        help_text="Nom de la colonne en base de données liée au filtre sur le territoire. Pour trouver le nom faire les mêmes étapes que pour geo_filter_id et chercher 'column' dans les paramètres json du native filter.",
    )
    mesh = models.TextField(
        choices=MeshLevel.choices,
        null=True,
        blank=True,
        help_text="Maille du territoire sur lequel s'effectue le filtre.",
    )
