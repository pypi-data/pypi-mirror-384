import re

from django.apps import apps
from django.urls import reverse


def parse_header_navigation(header_navigation):
    """
    Retourne une liste de sections. Chaque section est soit :
    - {'title': 'Accueil', 'link': '/accueil/'}
    - {'title': 'À propos', 'links': [{'title': 'Présentation', 'link': '/presentation/'}]}
    """
    menu = []

    # Découpage robuste en blocs (rubriques), même s'il y a des \r, espaces, etc.
    blocks = re.split(r"\n\s*\n", header_navigation.strip())

    for block in blocks:
        lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
        if not lines:
            continue

        title = None
        links = []

        # Si la première ligne n’est pas un lien markdown, c’est le titre
        first_line = lines[0]
        match = re.match(r"\[(.+?)\]\((/.+?/)\)", first_line)
        if match:
            # Bloc sans titre
            links.append(
                {
                    "title": match.group(1).strip(),
                    "link": match.group(2).strip(),
                }
            )
            other_lines = lines[1:]
        else:
            # cas spécial superset
            if first_line == "superset":
                Dashboard = apps.get_model("superset_lib", "Dashboard")
                links = [
                    {
                        "title": d.label,
                        "link": reverse(
                            "website:superset", kwargs={"dashboard_name": d.short_name}
                        )
                        + "#header-navigation",
                    }
                    for d in Dashboard.objects.all().order_by("order")
                ]
                menu.append({"title": "Portraits de territoires", "links": links})
                continue
            # La première ligne est le titre
            title = first_line
            other_lines = lines[1:]

        # Parse les lignes suivantes comme liens
        for line in other_lines:
            match = re.match(r"\[(.+?)\]\((/.+?/)\)", line)
            if not match:
                raise ValueError(
                    f"La ligne « {line} » n’est pas un lien valide Markdown."
                )
            links.append(
                {
                    "title": match.group(1).strip(),
                    "link": match.group(2).strip(),
                }
            )

        # Construction finale
        if title:
            if not links:
                raise ValueError(f"La rubrique « {title} » ne contient aucun lien.")
            menu.append({"title": title, "links": links})
        elif len(links) == 1:
            menu.append(links[0])
        else:
            raise ValueError("Un groupe de plusieurs liens doit avoir un titre.")
    return menu


def parse_footer_navigation(footer_navigation):
    """
    Retourne une liste de liens : chacun est un dict avec :
    - title : texte à afficher
    - href : URL du lien
    - is_external : True/False
    """
    links = []
    for line in footer_navigation.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        match = re.match(r"\[(.+?)\]\((.+?)\)", line)
        if not match:
            raise ValueError(f"Ligne invalide dans le footer : « {line} »")

        title, href = match.group(1).strip(), match.group(2).strip()

        is_external = href.startswith("http")
        links.append(
            {
                "title": title,
                "href": href,
                "is_external": is_external,
            }
        )
    return links


def parse_markdown_link(text):
    text = text.strip()
    if not text:
        raise ValueError("Le lien est invalide (vide)")

    match = re.match(r"\[(.+?)\]\((.+?)\)", text)
    if not match:
        raise ValueError(f"Ligne invalide dans le footer : « {text} »")

    title, href = match.group(1).strip(), match.group(2).strip()
    return {"title": title, "href": href}
