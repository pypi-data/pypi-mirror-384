from django.db import models
from martor.models import MartorField

from territories_dashboard_lib.commons.models import CommonModel
from territories_dashboard_lib.website_lib.navigation import (
    parse_footer_navigation,
    parse_header_navigation,
    parse_markdown_link,
)
from territories_dashboard_lib.website_lib.static_content import (
    markdown_content_to_html,
)


class MainConf(CommonModel):
    title = models.TextField(
        verbose_name="Titre principal du site", default="Tableau de bord"
    )
    description = models.TextField(
        verbose_name="Description du site",
        null=True,
        blank=True,
        help_text="Utilisé pour la balise meta description du site et pour le relais sur les réseaux sociaux.",
    )
    entity = models.TextField(
        verbose_name="Entité qui possède le site",
        default="",
        help_text="Renseigner le nom de l'entité au même format que le logo officiel en respectant les mises à la ligne.",
    )
    header_navigation = models.TextField(
        verbose_name="Navigation du header",
        help_text="""Navigation du header, mettre les liens au format markdown avec un slash à la fin du lien, mettre une ligne vide entre chaque rubrique. <br/><br/>
        
        Une rubrique peut contenir un seul lien, ou bien plusiers, dans ce cas la rubrique sera sous forme de dropdown et il faut mettre un titre en premier. <br/><br/>Par exemple : <br/>
        <br/><br/>
        [Accueil](/accueil/)
        <br/><br/>
        [Indicateurs territoriaux](/indicateurs/)
        <br/><br/>
        À propos
        [Présentation](/presentation/)
        [Journal des versions](/journal/)
        """,
        default="",
    )
    footer_navigation = models.TextField(
        verbose_name="Navigation du footer",
        help_text="""Navigation du footer, mettre les liens au format markdown, un par ligne. <br/><br/>
    Si le lien est interne, commencer et terminer le lien par un slash comme "/accueil/"<br/><br/>
    Par exemple : <br/><br/>
    [Plan du site](/plan-site/)<br/>
    [Accessibilité](/accessibilite/)<br/>
    [Mentions légales](/mentions-legales/) <br/>
    """,
        default="",
    )
    contact_email = models.TextField(
        default=None, null=True, blank=True, verbose_name="Email de contact"
    )
    newsletter_link = models.TextField(
        default=None,
        null=True,
        blank=True,
        verbose_name="Lien d'inscription à la newsletter",
    )
    show_footer_contact_banner = models.BooleanField(
        default=False,
        verbose_name="Afficher une bannière de contact au-dessus du footer",
        help_text="Pour afficher la bannière, l'email de contact et le lien d'inscription à la newsletter doivent être renseignés.",
    )
    social_image_url = models.TextField(
        null=True,
        blank=True,
        verbose_name="Image de description",
        help_text="Lien d'une image (idéalement 1200x630px). Elle sera utilisée lors du partage sur les réseaux sociaux.",
    )

    @property
    def entity_breaklines(self):
        return self.entity.replace("\n", "<br/>")

    @property
    def parsed_header_navigation(self):
        return parse_header_navigation(self.header_navigation)

    @property
    def parsed_footer_navigation(self):
        return parse_footer_navigation(self.footer_navigation)

    def __str__(self):
        return "Configuration principale"

    class Meta:
        verbose_name = "Configuration principale"
        verbose_name_plural = "Configurations principales"


class LandingPage(CommonModel):
    title = models.TextField(verbose_name="Titre")
    body = MartorField(verbose_name="Contenu")
    button_link = models.TextField(
        verbose_name="Lien du bouton",
        help_text="Au format markdown, par exemple : <br/><br/>[découvrir les indicateurs](/indicateurs/)",
    )

    @property
    def body_html(self):
        return markdown_content_to_html(self.body)

    @property
    def button(self):
        return parse_markdown_link(self.button_link)

    class Meta:
        verbose_name = "Page d'accueil"
        verbose_name_plural = "Page d'accueil"

    def __str__(self):
        return "Page d'accueil"


class StaticPage(CommonModel):
    name = models.TextField(verbose_name="Nom de la page")
    url = models.TextField(
        verbose_name="Url de la page",
        help_text="En minuscule avec des espaces remplacés par des traits '-'.<br/>Par exemple : <br/><br/> indicateurs <br/> mentions-legales",
    )
    body = MartorField(verbose_name="Contenu")

    @property
    def body_html(self):
        return markdown_content_to_html(self.body)

    class Meta:
        verbose_name = "Page Statique"
        verbose_name_plural = "Pages Statiques"

    def __str__(self):
        return self.name


class GlossaryItem(CommonModel):
    word = models.TextField(verbose_name="Mot")
    definition = models.TextField(verbose_name="Définition")

    class Meta:
        verbose_name = "Définition"
        verbose_name_plural = "Page Lexique"
        ordering = ["word"]

    def __str__(self):
        return self.word


class NoticeBanner(CommonModel):
    title = models.CharField(max_length=64, verbose_name="Titre")
    description = models.CharField(max_length=255, verbose_name="Description")
    link_href = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        verbose_name="Lien",
        help_text="Le lien doit être un lien interne et commencer et terminer par '/', par exemple '/journal/",
    )
    link_text = models.CharField(
        null=True,
        blank=True,
        max_length=64,
        verbose_name="Intitulé du lien",
        help_text="à remplir seulement si un lien est spécifié",
    )

    class Meta:
        ordering = ["-created_at"]
