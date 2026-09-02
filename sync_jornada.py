import os
import time
import requests
from dotenv import load_dotenv
from scoring_engine import guardar_puntos_jornada

load_dotenv()

TOURNAMENT_ID = 11653
HEADERS = {
    "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
    "x-rapidapi-host": os.getenv("RAPIDAPI_HOST"),
}


def obtener_temporada_actual() -> tuple[int, str]:
    url = f"https://sportapi7.p.rapidapi.com/api/v1/unique-tournament/{TOURNAMENT_ID}/seasons"
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        raise Exception(
            f"Error al obtener temporada actual: {res.status_code}"
        )

    data = res.json()
    season = data["seasons"][0]
    return season["id"], season["name"]


def procesar_equipo_lineup(
    players_list: list, numero_jornada: int, equipo_id: int
) -> int:
    procesados = 0

    for item in players_list:
        player_info = item.get("player", {})
        stats_info = item.get("statistics", {})

        player_id = player_info.get("id")
        posicion = player_info.get("position", "")
        nombre = player_info.get("name") or player_info.get("shortName")

        if not player_id:
            continue

        stats = {
            "minutos": stats_info.get("minutesPlayed", 0),
            "goles": stats_info.get("goals", 0),
            "asistencias": stats_info.get("goalAssist", 0),
            "amarillas": stats_info.get("yellowCards", 0),
            "rojas": stats_info.get("redCards", 0),
            "goles_recibidos": stats_info.get("goalsConceded", 0),
            "penaltis_parados": stats_info.get("savedPenalties", 0),
            "penaltis_provocados": stats_info.get("penaltyWon", 0),
            "penaltis_fallados": stats_info.get("penaltyMissed", 0),
            "penaltis_cometidos": stats_info.get("penaltyConceded", 0),
            "autogoles": stats_info.get("ownGoals", 0),
        }

        guardar_puntos_jornada(
            jugador_id=player_id,
            numero_jornada=numero_jornada,
            stats=stats,
            posicion=posicion,
            nombre=nombre,
            equipo_id=equipo_id,
        )
        procesados += 1

    return procesados


def sincronizar_jornada(numero_jornada: int):
    season_id, season_name = obtener_temporada_actual()
    print(
        f"🏆 Sincronizando Fecha {numero_jornada} ({season_name} - ID: {season_id})..."
    )

    url_events = f"https://sportapi7.p.rapidapi.com/api/v1/unique-tournament/{TOURNAMENT_ID}/season/{season_id}/events/round/{numero_jornada}"
    res_events = requests.get(url_events, headers=HEADERS)

    if res_events.status_code != 200:
        print(f"❌ Error al consultar la fecha: {res_events.status_code}")
        return

    events = res_events.json().get("events", [])
    print(f"📅 Se encontraron {len(events)} partidos en la jornada.")

    partidos_procesados = 0

    for event in events:
        event_id = event.get("id")
        home_team_info = event.get("homeTeam", {})
        away_team_info = event.get("awayTeam", {})

        home_team = home_team_info.get("name")
        away_team = away_team_info.get("name")
        home_team_id = home_team_info.get("id")
        away_team_id = away_team_info.get("id")

        status = event.get("status", {}).get("type")

        if status != "finished":
            print(
                f" ⏳ Partido omitido (Estado: {status}): {home_team} vs {away_team}"
            )
            continue

        print(f" ⚽ Procesando: {home_team} vs {away_team} (Event ID: {event_id})")

        url_lineup = (
            f"https://sportapi7.p.rapidapi.com/api/v1/event/{event_id}/lineups"
        )
        res_lineup = requests.get(url_lineup, headers=HEADERS)

        if res_lineup.status_code != 200:
            print(
                f"  ⚠️ No se pudieron obtener estadísticas para el evento {event_id}"
            )
            continue

        lineup_data = res_lineup.json()
        home_players = lineup_data.get("home", {}).get("players", [])
        away_players = lineup_data.get("away", {}).get("players", [])

        c_home = procesar_equipo_lineup(
            home_players, numero_jornada, home_team_id
        )
        c_away = procesar_equipo_lineup(
            away_players, numero_jornada, away_team_id
        )

        partidos_procesados += 1
        print(
            f"   ✓ Registrados {c_home + c_away} futbolistas de este encuentro."
        )

        time.sleep(0.3)

    print(
        f"\n🎉 Sincronización finalizada. {partidos_procesados} partidos procesados con éxito."
    )


if __name__ == "__main__":
    sincronizar_jornada(numero_jornada=1)