import os
import time
import timeit
from .global_config import get_timer

def timer(func):
    """
    Décorateur pour mesurer le temps d'exécution d'une fonction et enregistrer ce temps dans un logger si activé.
    :param func: La fonction à décorer pour mesurer et enregistrer son temps d'exécution.
    :raises ValueError: Si aucun logger n'est défini dans les arguments de la fonction appelée.
    :return: La fonction décorée qui mesure le temps d'exécution.
    """
    def wrapper(*args, **kwargs):
        if get_timer():
            logger = kwargs.get('logger', None)
            if logger is None and args and hasattr(args[0], 'logger'):
                logger = args[0].logger
            if logger is None: raise ValueError("Pas de logger défini.")
            start_time = timeit.default_timer()
            result = func(*args, **kwargs)
            elapsed_time = timeit.default_timer() - start_time
            if logger is not None:
                logger.info(f"Temps d'exécution de {func.__name__}: {elapsed_time:.4f} secondes.")
            return result
        else:
            return func(*args, **kwargs)
    return wrapper

def set_timezone(tz = 'Europe/Paris'):
    os.environ['TZ'] = tz
    time.tzset()