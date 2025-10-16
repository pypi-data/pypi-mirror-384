import re


def is_valid_regex(pattern: str) -> bool:
    """feature
    :name: is_valid_regex
    :description: Vérifie si une chaîne de caractères est une expression régulière valide.
    :param pattern: chaîne représentant l’expression régulière à tester.
    :return: True si l’expression régulière est valide, False sinon.
    """
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False
