# Tableau de bord des indicateurs territoriaux

## Présentation

Bienvenue dans ce projet visant à faciliter la création de tableaux de bord territoriaux interactifs à partir de données d’indicateurs. Ce dispositif est composé de deux briques complémentaires :

### 1. `territories_dashboard_lib`

Une **librairie Django** réutilisable, contenant des applications modulaires pour afficher rapidement un tableau de bord d'indicateurs territoriaux. Elle permet d’analyser des données à différentes mailles géographiques : nationale, régionale, départementale, et communale.  
Elle comprend des fonctionnalités prêtes à l'emploi pour visualiser des données sur des thématiques comme la **mobilité durable**, la **rénovation énergétique** ou d'autres indicateurs liés au développement territorial.

### 2. `territories_dashboard_template`

Un **template de projet Django clef en main**, conçu pour permettre à des équipes techniques de démarrer rapidement leur propre tableau de bord. Ce template utilise la librairie `territories_dashboard_lib` comme fondation.  
Les utilisateurs peuvent cloner ce dépôt, l’adapter à leurs besoins, et configurer leur tableau de bord directement depuis l’interface d’administration (titre, organisme, pages de contenu statique, indicateurs à afficher...).

Le template constitue un **point de départ standard**, mais n’impose aucune restriction technique en dehors du choix de Django comme framework. Les développeurs sont libres d'étendre ou de modifier les composants selon leurs besoins.

### Prérequis

Pour utiliser la librairie ou le template, vous devez disposer de :

-   Une base de données PostgreSQL contenant les données des indicateurs territoriaux.
-   Une capacité à déployer une application Django (hébergement, serveur web, etc.).

Pour obtenir des informations détaillées sur les prérequis techniques ou les données :

-   **Marina Ribeiro** – Directrice de projet Mission Connaissance  
    marina.ribeiro@developpement-durable.gouv.fr
-   **Louise Columelli** – ECOLAB  
    louise.columelli@developpement-durable.gouv.fr
-   **Olivier Rousseau** – Expert données  
    olivier.rousseau@i-carre.net
-   **Bastien** – Développeur web  
    bastien@prune.sh

### Exemples de projets utilisant ce dispositif

-   [Tableau de bord des mobilités durables](https://mobilite-durable-tdb.din.developpement-durable.gouv.fr)
-   [Boussole énergétique de la rénovation des logements](https://boussole-renovation.din.developpement-durable.gouv.fr)

L’objectif de ce projet est d’**encourager la réutilisation** et l’**essaimage** de nouveaux tableaux de bord territoriaux, en mettant à disposition un socle technique commun, facilement adaptable et extensible.

## Structure de la librairie

La librairie est composée de plusieurs **applications Django** indépendantes et complémentaires :

### `website_lib`

Contient le code principal d’affichage des pages du tableau de bord :

-   **Templates HTML Django** : dans `website_lib/templates`, organisés par page.
-   **Fichiers statiques** (JS, CSS) : dans `website_lib/static`. Le JS est modulaire grâce à l’extension `.mjs`.
-   **Vues Django** : dans `website_lib/views`, associées aux templates et fichiers statiques.

### `tracking_lib`

Gère le **tracking backend** : enregistrement en base de données des visites de pages, avec leurs paramètres (indicateur sélectionné, territoire, etc.) pour permettre des analyses d’usage.

### `superset_lib`

Permet d’**intégrer des dashboards Superset** dans les pages du site.  
Superset est un outil permettant à des utilisateurs non techniques de construire des visualisations depuis une base de données.

### `geo_lib`

Permet d’**ajouter des couches géographiques** personnalisées (points, lignes, polygones) à la carte :

-   Points : ex. stationnements vélo.
-   Lignes : ex. pistes cyclables.
-   Polygones : ex. zones ZFE.

### `indicators_lib`

Contient le code pour l’accès et la requête des **données d’indicateurs** dans la base PostgreSQL dédiée.

### Composants React

Certaines visualisations complexes sont développées en **React** (ex. cartes interactives, diagrammes de Sankey).

-   Les composants sont dans `website_lib/react-components/`.
-   Le bundling est effectué via **Webpack**
-   Les composants React sont ensuite inclus dans les templates Django.
-   `cd website_lib/react-components && npm install && npm run webpack`

## Installation

La librairie est publiée sur PyPI. Elle s’installe dans un projet Django via le package manager uv :

`uv add territories_dashboard_lib`

### Figer la version en production

Pour éviter les mises à jour inattendues, il est conseillé de figer la version dans le fichier pyproject.toml :

```
# Par exemple :
territories_dashboard_lib == 1.0.3
```

### Développement local

Pour tester une version locale de la librairie (ex : modifications en cours) :

`uv add --editable ~/territories-dashboard/territories-dashboard-lib`

## Publication PyPI

Pour builder la librairie avant publication :

`uv run python -m build`

Pour déployer sur PyPI, vous devez :

1. Avoir un compte PyPI.

2. Être membre du projet sur PyPI.

3. Lancer : `uv run twine upload dist/*`
