#!/usr/bin/env python3
import sys
import os
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.clickhouse import clickhouse_client
from src.utils.logger import logger

def load_issues_from_db():
    query = """
    SELECT title, body, labels
    FROM github_analytics.issues
    WHERE length(labels) > 0
    """
    rows, columns = clickhouse_client.client.execute(query, with_column_types=True)
    df = pd.DataFrame(rows, columns=[col[0] for col in columns])
    return df

def prepare_data(df):
    # Usar título + cuerpo como texto
    df['text'] = df['title'] + ' ' + df['body'].fillna('')
    # Tomar la primera etiqueta (simplificación; en producción podrías tomar la más relevante o hacer multilabel)
    df['label'] = df['labels'].apply(lambda x: x[0] if x else None)
    df = df.dropna(subset=['label'])
    return df

def main():
    logger.info("Cargando issues desde ClickHouse...")
    df = load_issues_from_db()
    if df.empty:
        logger.error("No hay issues con etiquetas")
        return
    
    df = prepare_data(df)
    logger.info(f"Total issues con etiqueta: {len(df)}")
    
    # Ver distribución de etiquetas
    print(df['label'].value_counts())
    
    # Filtrar clases con pocos ejemplos (opcional)
    min_samples = 30
    valid_labels = df['label'].value_counts()[df['label'].value_counts() >= min_samples].index
    df = df[df['label'].isin(valid_labels)]
    logger.info(f"Clases con >= {min_samples} muestras: {list(valid_labels)}")
    
    X = df['text']
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000, stop_words='english')),
        ('clf', LogisticRegression(max_iter=1000))
    ])
    
    pipeline.fit(X_train, y_train)
    
    y_pred = pipeline.predict(X_test)
    print(classification_report(y_test, y_pred))
    
    # Guardar modelo
    model_path = 'models/issue_classifier.pkl'
    os.makedirs('models', exist_ok=True)
    joblib.dump(pipeline, model_path)
    logger.info(f"Modelo guardado en {model_path}")

if __name__ == '__main__':
    main()