from pathlib import Path

API_URL = "https://archive-api.open-meteo.com/v1/archive"

VARIABLES = ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"]

CIUDADES = {
    "sevilla": {"lat": 37.39, "lon": -5.99},
    "malaga": {"lat": 36.72, "lon": -4.42},
    "granada": {"lat": 37.18, "lon": -3.60},
    "cordoba": {"lat": 37.89, "lon": -4.78},
}

TIMEZONE = "Europe/Madrid"

RAW_DIR = Path("data/raw")

PROCESSED_DIR = Path("data/processed")
