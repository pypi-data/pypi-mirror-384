import time


# https://stackoverflow.com/questions/31771286/python-in-memory-cache-with-time-to-live
def get_lru_cache_ttl(seconds):
    """feature
    :name: get_lru_cache_ttl
    :description: Génère une clé temporelle qui change toutes les `seconds` secondes.
    :comment: Permet d'expirer automatiquement le cache LRU en fonction d'un TTL.
    :param seconds: Nombre de secondes.
    :return: Un entier qui change toutes les `seconds` secondes.
    """
    return round(time.time() / seconds)
