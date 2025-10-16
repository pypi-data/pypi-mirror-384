import functools

from django.http import HttpRequest
from pydantic import ValidationError

from prune_lib.commons.parse import get_data_from_request
from prune_lib.commons.responses import JsonStringResponse


def use_payload(payload_class):
    """feature
    :name: use_payload
    :description: Décorateur pour valider automatiquement le payload d’une requête avec Pydantic.
    :comment: Ce décorateur extrait les données d’une requête HTTP via ``get_data_from_request`` puis les valide à l’aide d’une classe Pydantic fournie en paramètre. Si les données sont valides, elles sont injectées dans la vue sous le nom ``payload``. En cas d’erreur de validation, la fonction retourne directement une réponse JSON contenant les détails de l’erreur, avec un code HTTP 400.
    :param payload_class: classe Pydantic utilisée pour la validation des données.
    :return: décorateur appliqué à une vue Django.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            data = get_data_from_request(request)

            try:
                payload = payload_class(**data)
            except ValidationError as e:
                return JsonStringResponse(e.json(), status=400)

            return func(request, *args, payload=payload, **kwargs)

        return wrapper

    return decorator
