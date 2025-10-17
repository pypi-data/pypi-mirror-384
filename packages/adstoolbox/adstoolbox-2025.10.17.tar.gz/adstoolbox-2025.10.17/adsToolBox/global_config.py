import requests

_timer_enabled = False  # Variable globale pour déterminer si le timer est actif ou non

def set_timer(state: bool):
    """
    Active ou désactive le timer
    :param state: détermine l'état du timer
    """
    global _timer_enabled
    _timer_enabled = state

def get_timer() -> bool:
    """
    récupère l'état du timer
    :return: l'état du timer
    """
    return _timer_enabled

def get_public_ip(timeout: int = 5) -> str:
    """
    Récupère l'adresse IP publique de la machine
    :param timeout: Délai max de la requête http en secondes
    """
    urls = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://checkup.amazonaws.com"
    ]
    for url in urls:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return response.text.strip()
        except requests.RequestException:
            continue
    raise RuntimeError("Impossible de récupérer l'adresse IP publique")