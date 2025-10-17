import os

import geoip2.database
from django.db import transaction

from prune_lib.logging import logger
from prune_lib.website.contact import get_client_ip


def _get_country_from_geolite(ip_address):
    """feature
    :name: _get_country_from_geolite
    :description: Récupère le code pays ISO à partir d’une adresse IP via GeoLite2.
    :param ip_address: adresse IP à géolocaliser.
    :return: code pays ISO à deux lettres (ex: "FR") ou "UNKNOWN" si non trouvé.
    """
    database_name = "GeoLite2-Country.mmdb"
    database_path = os.path.join(os.path.dirname(__file__), database_name)
    reader = geoip2.database.Reader(database_path)
    try:
        response = reader.country(ip_address)
        country = response.country.iso_code
    except geoip2.errors.AddressNotFoundError:
        logger.warning(f"IP address not found in the database: {ip_address}")
        country = "UNKNOWN"
    reader.close()
    return country


def get_country_of_ip(request, model):
    """feature
    :name: get_country_of_ip
    :description: Détermine le pays d’un utilisateur à partir de son IP et l’enregistre en base.
    :param request: objet HttpRequest du client.
    :param model: modèle Django qui stocke l’IP et le code pays.
    :return: code pays ISO du client.
    """
    ip_address = get_client_ip(request)

    with transaction.atomic():
        ip_geolocalisation, created = model.objects.get_or_create(
            ip_address=ip_address,
            defaults={"country_iso_code": _get_country_from_geolite(ip_address)},
        )
        if not created:
            ip_geolocalisation.number_of_connections += 1
            ip_geolocalisation.save()
    return ip_geolocalisation.country_iso_code
