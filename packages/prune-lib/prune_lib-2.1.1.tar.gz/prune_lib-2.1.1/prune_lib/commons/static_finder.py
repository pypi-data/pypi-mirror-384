from django.contrib.staticfiles.finders import AppDirectoriesFinder


class TemplateCSSFinder(AppDirectoriesFinder):
    """
    Finder for CSS files located within the templates directories.

    This finder allows CSS files located under the 'templates' directory to be collected
    as static files and served using Django’s {% static %} template tag. For example:
    <link rel="stylesheet" href="{% static 'website/pages/page.css' %}">

    To enable this finder, add it to the STATICFILES_FINDERS setting in your settings.py:

        STATICFILES_FINDERS = [
            "prune_lib.commons.static_finders.TemplateCSSFinder",
            ...
        ]
    """

    source_dir = "templates"

    def list(self, ignore_patterns):
        """feature
        :name: list
        :description: Liste les fichiers CSS présents dans les répertoires de templates.
        :comment: Cette fonction est utilisée par la classe TemplateCSSFinder afin de parcourir les fichiers disponibles et de ne retourner que ceux ayant l’extension .css.
        :param ignore_patterns: motifs de fichiers à ignorer lors du parcours.
        :return: un générateur qui fournit les chemins des fichiers CSS trouvés.
        """
        for path, storage in super().list(ignore_patterns):
            if path.endswith(".css"):
                yield path, storage

    def find(self, path, find_all=False, **kwargs):
        """feature
        :name: find
        :description: Recherche un fichier CSS spécifique dans les répertoires de templates.
        :comment: Cette fonction est utilisée par la classe TemplateCSSFinder pour localiser un fichier CSS donné.
        :param path: chemin du fichier recherché.
        :param find_all: si True, retourne tous les chemins correspondant au fichier trouvé.
        :return: None, un chemin ou une liste de chemins vers les fichiers CSS trouvés.
        """
        if not path.endswith(".css"):
            return [] if find_all else None

        return super().find(path, find_all=find_all)
