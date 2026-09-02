import os
import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()

TOURNAMENT_ID = 11653
HEADERS = {
    "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
    "x-rapidapi-host": os.getenv("RAPIDAPI_HOST"),
}


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT"),
    )


def obtener_y_guardar_equipos():
    # 1. Obtener las temporadas disponibles
    url_seasons = f"https://sportapi7.p.rapidapi.com/api/v1/unique-tournament/{TOURNAMENT_ID}/seasons"
    res_seasons = requests.get(url_seasons, headers=HEADERS)

    if res_seasons.status_code != 200:
        print(f"Error al consultar temporadas: {res_seasons.status_code}")
        return

    seasons_data = res_seasons.json()
    latest_season_id = seasons_data["seasons"][0]["id"]
    season_name = seasons_data["seasons"][0]["name"]
    print(f"Cargando equipos de la temporada: {season_name} (ID: {latest_season_id})")

    # 2. Obtener los equipos de esa temporada
    url_teams = f"https://sportapi7.p.rapidapi.com/api/v1/unique-tournament/{TOURNAMENT_ID}/season/{latest_season_id}/teams"
    res_teams = requests.get(url_teams, headers=HEADERS)

    if res_teams.status_code != 200:
        print(f"Error al consultar equipos: {res_teams.status_code}")
        return

    teams_data = res_teams.json().get("teams", [])
    print(f"Se encontraron {len(teams_data)} equipos.")

    # 3. Guardar en Supabase
    conn = get_db_connection()
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
        # Generar URL del escudo basada en la API
        escudo_url = (
            f"https://sportapi7.p.rapidapi.com/api/v1/team/{team_id}/image"
        )

        cursor.execute(sql_insert, (team_id, nombre, escudo_url))

    conn.commit()
    cursor.close()
    conn.close()

    print("¡Equipos insertados con éxito en la base de datos!")


if __name__ == "__main__":
    obtener_y_guardar_equipos()