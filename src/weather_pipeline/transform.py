import json
import logging
from datetime import date

import pandas as pd

from weather_pipeline.config import CIUDADES, RAW_DIR, TIMEZONE

logger = logging.getLogger(__name__)

COLUMNAS = {
    "time": "fecha",
    "temperature_2m_max": "temp_max_c",
    "temperature_2m_min": "temp_min_c",
    "precipitation_sum": "precipitacion_mm",
}


def transformar_dia(fecha: date) -> pd.DataFrame:
    """Transforma los datos descargados en un DataFrame de pandas."""
    dia = fecha.isoformat()
    raw_dir = RAW_DIR / f"fecha={dia}"
    archivos = list(raw_dir.glob("*.json"))
    if not archivos:
        raise ValueError(f"No hay archivos JSON en {raw_dir}")

    dfs = []
    fecha_carga = pd.Timestamp.now(tz=TIMEZONE)
    for archivo in archivos:
        ciudad = archivo.stem
        with open(archivo, "r", encoding="utf-8") as f:
            datos = json.load(f)
        df_ciudad = pd.DataFrame(datos["daily"]).rename(columns=COLUMNAS)
        df_ciudad["ciudad"] = ciudad
        df_ciudad["fecha"] = pd.to_datetime(df_ciudad["fecha"])
        df_ciudad["fecha_carga"] = fecha_carga
        df_ciudad = df_ciudad.reindex(
            columns=[
                "ciudad",
                "fecha",
                "temp_max_c",
                "temp_min_c",
                "precipitacion_mm",
                "fecha_carga",
            ]
        )
        dfs.append(df_ciudad)

    df_final = pd.concat(dfs, ignore_index=True)

    logger.info("Transformación completada para %s", dia)
    logger.info("Número de filas: %d", len(df_final))
    return df_final


def _describir_filas(df: pd.DataFrame, mascara: pd.Series, *columnas: str) -> str:
    """Describe las filas marcadas por la máscara: ciudad, fecha y valor de las columnas indicadas."""
    partes = []
    for _, fila in df[mascara].iterrows():
        detalle = [
            f"{fila['fecha']:%Y-%m-%d}" if pd.notna(fila["fecha"]) else "fecha nula"
        ]
        detalle += [f"{columna}={fila[columna]}" for columna in columnas]
        partes.append(f"{fila['ciudad']} ({', '.join(detalle)})")
    return "; ".join(partes)


def validar(df: pd.DataFrame, fecha: date) -> None:
    """Valida el DataFrame resultante. Lanza ValueError con todos los problemas encontrados."""
    fallidos = []

    for columna in df.columns[df.isnull().any()]:
        mascara = df[columna].isnull()
        fallidos.append(
            f"Valores nulos en '{columna}': {_describir_filas(df, mascara)}"
        )

    mascara = df["temp_max_c"] < df["temp_min_c"]
    if mascara.any():
        fallidos.append(
            "Temperatura máxima menor que la mínima: "
            + _describir_filas(df, mascara, "temp_max_c", "temp_min_c")
        )

    mascara = (df["temp_max_c"] > 55) | (df["temp_max_c"] < -30)
    if mascara.any():
        fallidos.append(
            "Temperatura máxima por encima de 55 °C o por debajo de -30 °C: "
            + _describir_filas(df, mascara, "temp_max_c")
        )

    mascara = (df["temp_min_c"] < -30) | (df["temp_min_c"] > 55)
    if mascara.any():
        fallidos.append(
            "Temperatura mínima por debajo de -30 °C o por encima de 55 °C: "
            + _describir_filas(df, mascara, "temp_min_c")
        )

    mascara = df["precipitacion_mm"] < 0
    if mascara.any():
        fallidos.append(
            "Precipitación negativa: "
            + _describir_filas(df, mascara, "precipitacion_mm")
        )

    mascara = df["fecha"].dt.date != fecha
    if mascara.any():
        fallidos.append(
            f"Filas con fecha distinta de {fecha}: {_describir_filas(df, mascara)}"
        )

    esperadas = set(CIUDADES)
    presentes = set(df["ciudad"].dropna())
    faltan = sorted(esperadas - presentes)
    if faltan:
        fallidos.append(f"Faltan ciudades: {', '.join(faltan)}")
    sobran = sorted(presentes - esperadas)
    if sobran:
        fallidos.append(f"Ciudades no configuradas en CIUDADES: {', '.join(sobran)}")

    filas_por_ciudad = df["ciudad"].value_counts()
    repetidas = filas_por_ciudad[filas_por_ciudad > 1]
    if not repetidas.empty:
        fallidos.append(
            "Ciudades con más de una fila: "
            + ", ".join(f"{ciudad} ({n} filas)" for ciudad, n in repetidas.items())
        )

    if fallidos:
        plural = "s" if len(fallidos) > 1 else ""
        raise ValueError(
            f"Validación fallida para {fecha} ({len(fallidos)} problema{plural}):\n- "
            + "\n- ".join(fallidos)
        )
