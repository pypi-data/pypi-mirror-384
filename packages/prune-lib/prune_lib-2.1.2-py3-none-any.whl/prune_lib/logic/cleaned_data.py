import re


def clean_phone(phone: str) -> str | None:
    """feature
    :name: clean_phone
    :description: Valide et normalise un numéro de téléphone simple.
    :param phone: numéro de téléphone à valider.
    :return: le numéro de téléphone inchangé s’il est valide, ValueError si pas valide.
    """
    if phone and not re.match(r"^[\d\+\- \(\)]{6,20}$", phone):
        raise ValueError("invalid_phone_number")
    return phone
