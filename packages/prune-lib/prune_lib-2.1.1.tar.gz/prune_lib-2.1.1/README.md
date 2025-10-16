# prune_lib

prune_lib est une bibliothèque Python regroupant des fonctions utilitaires réutilisables.  
L’objectif est de faciliter le développement de projets en centralisant des outils communs.

Le projet inclut aussi prune_captcha, un module dédié à l’ajout d’un CAPTCHA personnalisé dans les formulaires de contact.

## Projet UV

### Installation

Lancez la commande suivante dans le terminal :

```bash
uv add prune_lib
```

### Mise à jour de la bilbiothèque

N’hésitez pas à exécuter régulièrement uv sync --upgrade, car la bibliothèque évolue avec le temps et nos pratiques !

## Projet Poetry

### Installation

Lancez la commande suivante :

```bash
poetry add prune_lib
```

### Mise à jour de la bibliothèque

N’hésitez pas à exécuter régulièrement poetry update, car la bibliothèque évolue avec le temps et nos pratiques !

## Objectifs

-   Réutiliser facilement des fonctions communes.
-   Fournir une alternative simple à reCAPTCHA.
-   Ne dépendre d’aucun service externe.

## Intégration du captcha

### Configuration

Dans `settings.py`, définis le chemin des images utilisées pour le puzzle :

```python
PUZZLE_IMAGE_STATIC_PATH = "website/static/website/images/puzzles/"
```

Important : Tu dois importer les fichiers statiques (css, js) présents dans "prune_captcha/static/".

```html
<header>
    <link
        rel="stylesheet"
        href="{% static 'prune_captcha/css/captcha.css' %}"
    />
    <script defer src="{% static 'prune_captcha/js/captcha.js' %}"></script>
</header>
```

### Utilisation

-   Requête GET (affichage du formulaire)

    -   Utilise create_and_get_captcha pour générer les données du captcha :

        ```python
        from prune_captcha.utils import create_and_get_captcha
        ```

        ```python
        puzzle = create_and_get_captcha(request)
        ```

    -   Passe les données dans le contexte sous la variable puzzle :

        ```python
        return render(
            request,
            "website/pages/contact/page.html",
            {"form": form, "puzzle": puzzle},
        )
        ```

    -   Inclus le composant dans ton template :

        ```
        {% include "prune_captcha/captcha.html" %}
        ```

-   Requête POST (soumission du formulaire)

    -   Utilise verify_captcha pour valider le captcha :

        ```python
        from prune_captcha.utils import verify_captcha
        ```

        ```python
        response = verify_captcha(request)
        ```

    -   True si le captcha est correct, sinon False.

    -   Redirige en cas de captcha incorrect.
