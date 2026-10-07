import time
from database import get_raw_db_connection
from scoring_engine import guardar_puntos_jornada
from sportapi import (
    TOURNAMENT_ID,
    api_get,
    obtener_season_actual,
    asegurar_tablas_sync,
)


def evento_ya_sincronizado(event_id: int) -> bool:
    conn = get_raw_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT 1 FROM eventos_sincronizados WHERE event_id = %s;",
            (event_id,),
        )
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()


def marcar_evento_sincronizado(event_id: int, numero_jornada: int):
    conn = get_raw_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO eventos_sincronizados (event_id, numero_jornada)
            VALUES (%s, %s)
            ON CONFLICT (event_id) DO NOTHING;
            """,
            (event_id, numero_jornada),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


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


def sincronizar_jornada(numero_jornada: int) -> dict:
    """Sincroniza los puntos de una jornada desde SportAPI7.

    Devuelve un resumen con partidos totales, procesados y pendientes
    (e.g. en juego o aún no programados), para que el llamador decida
    si la jornada puede marcarse como FINALIZADA.
    """
    asegurar_tablas_sync()
    season_id, season_name = obtener_season_actual()
    print(
        f"🏆 Sincronizando Fecha {numero_jornada} ({season_name} - ID: {season_id})..."
    )

    events = api_get(
        f"/unique-tournament/{TOURNAMENT_ID}/season/{season_id}/events/round/{numero_jornada}"
    ).get("events", [])
    print(f"📅 Se encontraron {len(events)} partidos en la jornada.")

    resumen = {
        "partidos_total": len(events),
        "partidos_procesados": 0,
        "partidos_pendientes": 0,
        "partidos_reutilizados": 0,
        "jugadores_registrados": 0,
    }

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
                f" ⏳ Partido pendiente ({status}): {home_team} vs {away_team}"
            )
            resumen["partidos_pendientes"] += 1
            continue

        if evento_ya_sincronizado(event_id):
            print(
                f" ♻️ Ya sincronizado (sin request): {home_team} vs {away_team}"
            )
            resumen["partidos_reutilizados"] += 1
            resumen["partidos_procesados"] += 1
            continue

        print(f" ⚽ Procesando: {home_team} vs {away_team} (Event ID: {event_id})")

        lineup_data = api_get(f"/event/{event_id}/lineups")
        home_players = lineup_data.get("home", {}).get("players", [])
        away_players = lineup_data.get("away", {}).get("players", [])

        c_home = procesar_equipo_lineup(
            home_players, numero_jornada, home_team_id
        )
        c_away = procesar_equipo_lineup(
            away_players, numero_jornada, away_team_id
        )

        marcar_evento_sincronizado(event_id, numero_jornada)

        resumen["partidos_procesados"] += 1
        resumen["jugadores_registrados"] += c_home + c_away
        print(
            f"   ✓ Registrados {c_home + c_away} futbolistas de este encuentro."
        )

        time.sleep(0.3)

    print(
        f"\n🎉 Sincronización de la Fecha {numero_jornada} finalizada: "
        f"{resumen['partidos_procesados']}/{resumen['partidos_total']} partidos "
        f"({resumen['partidos_pendientes']} pendientes)."
    )
    return resumen


if __name__ == "__main__":
    sincronizar_jornada(numero_jornada=1)