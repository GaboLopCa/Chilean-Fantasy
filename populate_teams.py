import os
from dotenv import load_dotenv
from database import get_raw_db_connection
from sportapi import TOURNAMENT_ID, api_get, obtener_season_actual, asegurar_tablas_sync

load_dotenv()


def obtener_y_guardar_equipos():
    # 1. Temporada (cacheada en BD; solo consume 1 request la primera vez)
    season_id, season_name = obtener_season_actual()
    print(f"Cargando equipos de la temporada: {season_name} (ID: {season_id})")

    # 2. Obtener los equipos de esa temporada
    teams_data = api_get(
        f"/unique-tournament/{TOURNAMENT_ID}/season/{season_id}/teams"
    ).get("teams", [])
    print(f"Se encontraron {len(teams_data)} equipos.")

    # 3. Guardar en Supabase
    conn = get_raw_db_connection()
    cursor = conn.cursor()

    sql_insert = """
        INSERT INTO equipos (id, nombre, escudo_url)
        VALUES (%s, %s, %s)
        ON CONFLICT (id) DO UPDATE 
        SET nombre = EXCLUDED.nombre, escudo_url = EXCLUDED.escudo_url;
    """

    for team in teams_data:
        team_id = team["id"]
        nombre = team.get("name")
        escudo_url = (
            f"https://sportapi7.p.rapidapi.com/api/v1/team/{team_id}/image"
        )

        cursor.execute(sql_insert, (team_id, nombre, escudo_url))

    conn.commit()
    cursor.close()
    conn.close()

    print("¡Equipos insertados con éxito en la base de datos!")


if __name__ == "__main__":
    asegurar_tablas_sync()
    obtener_y_guardar_equipos()