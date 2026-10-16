import logging
from datetime import date

import requests

from weather_pipeline.config import API_URL, CIUDADES, VARIABLES

logger = logging.getLogger(__name__)

TIMEOUT_SEGUNDOS = 10


def descargar_dia(ciudad: str, fecha: date) -> dict:
    """Descarga los datos diarios de una ciudad para un día concreto."""
    coordenadas = CIUDADES[ciudad]
    dia = fecha.isoformat()

    logger.info("Descargando datos de %s para %s", ciudad, dia)

    params = {
        "latitude": coordenadas["lat"],
        "longitude": coordenadas["lon"],
        "start_date": dia,
        "end_date": dia,
        "daily": ",".join(VARIABLES),
        "timezone": "Europe/Madrid",
    }
    response = requests.get(API_URL, params=params, timeout=TIMEOUT_SEGUNDOS)
    response.raise_for_status()
    datos = response.json()

    logger.info("Descarga completada para %s el %s", ciudad, dia)
    return datos
