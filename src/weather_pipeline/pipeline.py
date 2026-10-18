import argparse
import logging
import sys
from datetime import date, timedelta

from weather_pipeline.ingest import ingestar_dia
from weather_pipeline.load import guardar_processed
from weather_pipeline.transform import transformar_dia, validar

logger = logging.getLogger(__name__)


def ejecutar_dia(fecha: date) -> None:
    """Ejecuta la pipeline completa para un día concreto."""

    logger.info("Ejecutando pipeline para %s", fecha)

    # Ingest
    ingestar_dia(fecha)

    # Transform
    df = transformar_dia(fecha)

    # Validar
    validar(df, fecha)

    # Load
    guardar_processed(df, fecha)

    logger.info("Pipeline completada para %s", fecha)


def main() -> None:
    """Ejecuta el pipeline para un rango de fechas."""
    parser = argparse.ArgumentParser(description="Pipeline de datos meteorológicos")
    parser.add_argument(
        "--desde",
        type=date.fromisoformat,
        required=True,
        help="Primer día a procesar (AAAA-MM-DD)",
    )
    parser.add_argument(
        "--hasta",
        type=date.fromisoformat,
        required=True,
        help="Último día a procesar (AAAA-MM-DD)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    desde = args.desde
    hasta = args.hasta

    errores = []

    fecha_actual = desde
    while fecha_actual <= hasta:
        try:
            ejecutar_dia(fecha_actual)
        except (RuntimeError, ValueError) as e:
            logger.exception("Error procesando %s", fecha_actual)
            errores.append((fecha_actual, e))
        fecha_actual = fecha_actual + timedelta(days=1)

    if errores:
        logger.error("Errores encontrados en los siguientes días:")
        for fecha, error in errores:
            logger.error("  %s: %s", fecha, error)
        sys.exit(1)


if __name__ == "__main__":
    main()
