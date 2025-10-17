from django.http import HttpRequest

from prune_lib.captcha import verify_captcha
from prune_lib.website.contact import (
    RateLimitError,
    check_rate_limit,
)


def verify_form_with_captcha_and_rate_limit(
    request: HttpRequest, contact_form_response
) -> bool:
    """feature
    :name: verify_form_with_captcha_and_rate_limit
    :description: Vérifie si un formulaire peut être soumis en validant le CAPTCHA et les limites par ip.
    :param request: objet HttpRequest de la soumission.
    :param contact_form_response: form Django représentant les réponses du formulaire.
    :return: True si la soumission est autorisée, False sinon.
    """
    captcha_ok = verify_captcha(request)
    if captcha_ok:
        try:
            check_rate_limit(request, contact_form_response)
        except RateLimitError:
            return False
        else:
            return True
    else:
        return False
