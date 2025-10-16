from django.http import HttpRequest
from django.utils import timezone


class RateLimitError(Exception):
    pass


def get_client_ip(request: HttpRequest) -> str | None:
    """feature
    :name: get_client_ip
    :description: Récupère l’adresse IP du client à partir d’une requête Django.
    :param request: HttpRequest contenant les informations de connexion du client.
    :return: adresse IP du client sous forme de chaîne, ou None si introuvable.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def check_rate_limit(request: HttpRequest, contact_form_response) -> None:
    """feature
    :name: check_rate_limit
    :description: Vérifie si un utilisateur a dépassé le quota de soumissions d’un formulaire.
    :comment:
        - Limite globale : maximum 100 soumissions par jour.
        - Limite par IP : maximum 5 soumissions par IP et par jour.
        - Lève une exception RateLimitError si une limite est dépassée.
    :param request: objet HttpRequest du client.
    :param contact_form_response: form Django correspondant aux réponses du formulaire.
    :return: None, mais lève RateLimitError en cas de dépassement.
    """
    ip_address = get_client_ip(request)
    today = timezone.now().date()

    total_submissions_today = contact_form_response.objects.filter(
        created_at__date=today
    ).count()
    if total_submissions_today >= 100:
        raise RateLimitError

    submissions_by_ip_today = contact_form_response.objects.filter(
        created_at__date=today, ip_address=ip_address
    ).count()
    if submissions_by_ip_today >= 5:
        raise RateLimitError
