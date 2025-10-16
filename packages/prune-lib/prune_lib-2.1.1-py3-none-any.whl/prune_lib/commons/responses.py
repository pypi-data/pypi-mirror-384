from django.http import HttpResponse


class JsonStringResponse(HttpResponse):
    """feature
    :name: JsonStringResponse
    :description: Réponse HTTP spécialisée pour retourner du contenu JSON sous forme de chaîne.
    :param content: contenu JSON déjà sérialisé en chaîne.
    :return: un objet HttpResponse avec le bon Content-Type.
    """

    def __init__(self, content, *args, **kwargs):
        kwargs["content_type"] = "application/json"
        super().__init__(content, *args, **kwargs)
