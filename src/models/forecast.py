# src/models/forecast.py
from datetime import datetime

import pandas as pd
from prophet import Prophet

from src.database.clickhouse import clickhouse_client
from src.utils.logger import logger


def train_and_forecast(repo_name: str, periods: int = 30):
    """
    Entrena un modelo Prophet con datos históricos de eventos y genera predicciones.
    """
    logger.info(f"Entrenando modelo para {repo_name}...")

    # 1. Obtener datos históricos de la tabla events
    query = f"""
        SELECT
            toDate(created_at) as ds,
            count() as y
        FROM github_analytics.events
        WHERE repo_name = '{repo_name}'
        GROUP BY ds
        ORDER BY ds
    """
    result = clickhouse_client.client.execute(query, with_column_types=True)
    # Convertir a DataFrame
    df = pd.DataFrame(result[0], columns=[col[0] for col in result[1]])

    if df.empty:
        logger.warning(f"No hay datos históricos para {repo_name}")
        return None

    # 2. Entrenar modelo Prophet
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        interval_width=0.95,
    )
    model.fit(df)

    # 3. Generar fechas futuras (sin incluir el histórico)
    future = model.make_future_dataframe(periods=periods, include_history=False)

    # 4. Predecir
    forecast = model.predict(future)

    # 5. Preparar resultados para guardar en forecasts
    predictions = []
    for _, row in forecast.iterrows():
        predictions.append(
            {
                "repository": repo_name,
                "forecast_date": row["ds"].date(),
                "predicted_events": int(
                    max(0, row["yhat"])
                ),  # Aseguramos que no sea negativo
                "lower_bound": int(max(0, row["yhat_lower"])),
                "upper_bound": int(max(0, row["yhat_upper"])),
                "model_type": "prophet",
                "training_date": datetime.now().date(),
            }
        )

    logger.info(f"Predicciones generadas para {repo_name}")
    return predictions


def save_predictions(predictions: list):
    """Guarda las predicciones en ClickHouse en la tabla forecasts."""
    if not predictions:
        return

    query = """
    INSERT INTO github_analytics.forecasts
    (repository, forecast_date, predicted_events, lower_bound, upper_bound, model_type, training_date)
    VALUES
    """
    values = [
        (
            p["repository"],
            p["forecast_date"],
            p["predicted_events"],
            p["lower_bound"],
            p["upper_bound"],
            p["model_type"],
            p["training_date"],
        )
        for p in predictions
    ]

    clickhouse_client.client.execute(query, values)
    logger.info(f"{len(predictions)} predicciones guardadas en ClickHouse")
