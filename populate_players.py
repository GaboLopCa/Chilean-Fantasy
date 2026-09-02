import os
import time
import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()

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


def obtener_y_guardar_jugadores():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Obtener la lista de IDs de equipos guardados en la base de datos
    cursor.execute("SELECT id, nombre FROM equipos;")
    equipos = cursor.fetchall()

    if not equipos:
        print(
            "No se encontraron equipos en la base de datos. Ejecuta primero populate_teams.py."
        )
        return

    print(f"Obteniendo plantilla para {len(equipos)} equipos...")

    sql_insert_jugador = """
        INSERT INTO jugadores (id, nombre, posicion, equipo_id, foto_url)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE 
        SET nombre = EXCLUDED.nombre, 
            posicion = EXCLUDED.posicion, 
            equipo_id = EXCLUDED.equipo_id, 
            foto_url = EXCLUDED.foto_url;
    """

    total_jugadores = 0

    # 2. Iterar sobre cada equipo para consultar sus jugadores
    for equipo_id, equipo_nombre in equipos:
        url_players = (
            f"https://sportapi7.p.rapidapi.com/api/v1/team/{equipo_id}/players"
        )
        res_players = requests.get(url_players, headers=HEADERS)

        if res_players.status_code != 200:
            print(
                f"⚠️ Error al obtener jugadores de {equipo_nombre}: {res_players.status_code}"
            )
            continue

        players_data = res_players.json().get("players", [])

        for item in players_data:
            player = item.get("player", {})
            player_id = player.get("id")
            nombre = player.get("name") or player.get("shortName")
            posicion = player.get("position", "N/A")
            foto_url = (
                f"https://sportapi7.p.rapidapi.com/api/v1/player/{player_id}/image"
                if player_id
                else None
            )

            if player_id and nombre:
                cursor.execute(
                    sql_insert_jugador,
                    (player_id, nombre, posicion, equipo_id, foto_url),
                )
                total_jugadores += 1

        print(
            f"  ✓ {equipo_nombre}: {len(players_data)} jugadores procesados."
        )
        # Breve pausa para evitar saturar el límite de peticiones por segundo
        time.sleep(0.2)

    conn.commit()
    cursor.close()
    conn.close()

    print(
        f"\n🎉 ¡Proceso completado! Se registraron {total_jugadores} jugadores en Supabase."
    )


if __name__ == "__main__":
    obtener_y_guardar_jugadores()