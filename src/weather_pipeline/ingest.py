import json
import logging
from datetime import date
from pathlib import Path

import requests

from weather_pipeline.config import API_URL, CIUDADES, RAW_DIR, TIMEZONE, VARIABLES

logger = logging.getLogger(__name__)

TIMEOUT_SEGUNDOS = 10


def descargar_dia(ciudad: str, fecha: date) -> dict:
    """Descarga los datos diarios de una ciudad para un día concreto."""
    if ciudad not in CIUDADES:
        raise ValueError(
            f"Ciudad desconocida: {ciudad!r}. Disponibles: {', '.join(sorted(CIUDADES))}"
        )
    coordenadas = CIUDADES[ciudad]
    dia = fecha.isoformat()

    logger.info("Descargando datos de %s para %s", ciudad, dia)

    params = {
        "latitude": coordenadas["lat"],
        "longitude": coordenadas["lon"],
        "start_date": dia,
        "end_date": dia,
        "daily": ",".join(VARIABLES),
        "timezone": TIMEZONE,
    }
    response = requests.get(API_URL, params=params, timeout=TIMEOUT_SEGUNDOS)
    response.raise_for_status()
    datos = response.json()

    logger.info("Descarga completada para %s el %s", ciudad, dia)
    return datos


def guardar_raw(datos: dict, ciudad: str, fecha: date) -> Path:
    """Guarda los datos descargados en un archivo JSON."""

    dia = fecha.isoformat()
    raw_dir = RAW_DIR / f"fecha={dia}"
    raw_dir.mkdir(parents=True, exist_ok=True)
    archivo_tmp = raw_dir / f"{ciudad}.json.tmp"
    archivo = raw_dir / f"{ciudad}.json"

    with open(archivo_tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

    archivo_tmp.replace(
        archivo
    )  # Escritura atómica: si el proceso muere antes, nunca queda un JSON a medias

    logger.info("Datos guardados en %s", archivo)

    return archivo


def ingestar_dia(fecha: date) -> list[Path]:
    """Descarga y guarda los datos de todas las ciudades para un día concreto."""
    raw_paths = []
    fallidos = []
    for ciudad in CIUDADES:
        try:
            datos = descargar_dia(ciudad, fecha)
            raw_path = guardar_raw(datos, ciudad, fecha)
            raw_paths.append(raw_path)
        except requests.RequestException:
            logger.exception("Error al procesar %s para %s", ciudad, fecha)
            fallidos.append(ciudad)
    if fallidos:
        raise RuntimeError(
            f"Fallaron {len(fallidos)} de {len(CIUDADES)} ciudades para {fecha}: {', '.join(fallidos)}"
        )
    return raw_paths
