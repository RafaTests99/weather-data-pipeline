import logging
from datetime import date
from pathlib import Path

import pandas as pd

from weather_pipeline.config import PROCESSED_DIR

logger = logging.getLogger(__name__)


def guardar_processed(df: pd.DataFrame, fecha: date) -> Path:
    """Guarda el DataFrame procesado en un archivo Parquet."""

    dia = fecha.isoformat()
    processed_dir = PROCESSED_DIR / f"fecha={dia}"
    processed_dir.mkdir(parents=True, exist_ok=True)
    archivo_tmp = processed_dir / "datos.parquet.tmp"
    archivo = processed_dir / "datos.parquet"

    df.to_parquet(archivo_tmp, index=False)

    # Escritura atómica: si el proceso muere antes, nunca queda un Parquet a medias
    archivo_tmp.replace(archivo)

    logger.info("Datos procesados guardados en %s", archivo)
    logger.info("Número de filas guardadas: %d", len(df))

    return archivo
