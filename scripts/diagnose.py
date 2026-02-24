#!/usr/bin/env python3
"""
Diagnostica la presencia de datos en ClickHouse para ayudar a resolver problemas de "No data".
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.clickhouse import clickhouse_client

def print_query(query, description):
    try:
        result = clickhouse_client.execute_query(query)
        if result:
            print(f"✅ {description}: {result[0][0]}")
        else:
            print(f"⚠️ {description}: 0 o vacío")
    except Exception as e:
        print(f"❌ {description}: ERROR - {e}")

def main():
    print("\n🔍 DIAGNÓSTICO DE DATOS EN CLICKHOUSE\n" + "="*40)

    # Totales generales
    print_query("SELECT count() FROM github_analytics.events", "Total events")
    print_query("SELECT count() FROM github_analytics.issues", "Total issues")
    print_query("SELECT count() FROM github_analytics.forecasts", "Total forecasts")

    # Últimos 7 días
    print_query("SELECT count() FROM github_analytics.events WHERE created_at >= now() - interval 7 day", "Events last 7d")
    print_query("SELECT count() FROM github_analytics.issues WHERE created_at >= now() - interval 7 day", "Issues last 7d")

    # Últimos 30 días
    print_query("SELECT count() FROM github_analytics.events WHERE created_at >= now() - interval 30 day", "Events last 30d")
    print_query("SELECT count() FROM github_analytics.issues WHERE created_at >= now() - interval 30 day", "Issues last 30d")

    # Repositorios disponibles
    repos = clickhouse_client.execute_query("SELECT DISTINCT repo_name FROM github_analytics.events LIMIT 5")
    if repos:
        print(f"\n📌 Repositorios (muestra): {[r[0] for r in repos]}")
    else:
        print("\n⚠️ No hay repositorios en events.")

    # Issues cerrados con datos de tiempo
    print_query("SELECT count() FROM github_analytics.issues WHERE state='closed' AND closed_at IS NOT NULL", "Closed issues with closed_at")

    # Eventos de tipo PullRequestEvent con merges
    print_query("SELECT count() FROM github_analytics.events WHERE type='PullRequestEvent' AND payload LIKE '%merged%'", "Merged PR events")

    print("\n" + "="*40)
    print("Si alguna métrica es 0, ejecuta 'make run-etl' y 'make train-model' para poblar datos.\n")

if __name__ == '__main__':
    main()