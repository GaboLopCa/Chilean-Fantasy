import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT"),
    )


def calcular_puntos(stats: dict, posicion: str) -> int:
    """Calcula el puntaje acumulado con base en las reglas de LaLiga Fantasy."""
    puntos = 0
    pos = (posicion or "").upper()

    minutos = stats.get("minutos", 0)
    goles = stats.get("goles", 0)
    asistencias = stats.get("asistencias", 0)
    amarillas = stats.get("amarillas", 0)
    rojas = stats.get("rojas", 0)
    goles_recibidos = stats.get("goles_recibidos", 0)
    penaltis_parados = stats.get("penaltis_parados", 0)
    penaltis_provocados = stats.get("penaltis_provocados", 0)
    penaltis_fallados = stats.get("penaltis_fallados", 0)
    penaltis_cometidos = stats.get("penaltis_cometidos", 0)
    autogoles = stats.get("autogoles", 0)

    # 1. Minutos jugados
    if minutos >= 60:
        puntos += 2
    elif minutos > 0:
        puntos += 1

    # 2. Goles anotados según posición
    if pos in ["F", "FW", "ST", "ATT"]:
        puntos += goles * 4
    elif pos in ["M", "MF", "MID"]:
        puntos += goles * 5
    elif pos in ["D", "DF", "DEF"]:
        puntos += goles * 6
    elif pos in ["G", "GK"]:
        puntos += goles * 6
    else:
        puntos += goles * 4

    # 3. Asistencias
    puntos += asistencias * 3

    # 4. Portería a cero (solo si jugó 60 minutos o más)
    if minutos >= 60 and goles_recibidos == 0:
        if pos in ["G", "GK", "D", "DF", "DEF"]:
            puntos += 4
        elif pos in ["M", "MF", "MID"]:
            puntos += 1

    # 5. Penalizaciones por goles encajados (Porteros y Defensas)
    if pos in ["G", "GK", "D", "DF", "DEF"]:
        puntos -= goles_recibidos // 2

    # 6. Eventos de Penaltis
    puntos += penaltis_parados * 5
    puntos += penaltis_provocados * 2
    puntos -= penaltis_fallados * 2
    puntos -= penaltis_cometidos * 2

    # 7. Sanciones e Infracciones
    puntos -= autogoles * 2
    puntos -= amarillas * 1
    puntos -= rojas * 3

    # Dentro del proceso de cálculo de scoring por usuario:
    cursor.execute("SELECT saldo FROM usuarios WHERE id = %s;", (usuario_id,))
    saldo_usuario = cursor.fetchone()["saldo"]

    if saldo_usuario < 0:
        puntos_totales_jornada = 0  # Sanción automática de LaLiga Fantasy

    return puntos

def guardar_puntos_jornada(
    jugador_id: int,
    numero_jornada: int,
    stats: dict,
    posicion: str,
    nombre: str = None,
    equipo_id: int = None,
):
    """Guarda o actualiza las estadísticas y puntos del jugador para una jornada específica."""
    puntos_totales = calcular_puntos(stats=stats, posicion=posicion)

    conn = get_db_connection()
    cursor = conn.cursor()

    if nombre and equipo_id:
        foto_url = (
            f"https://sportapi7.p.rapidapi.com/api/v1/player/{jugador_id}/image"
        )
        sql_insert_jugador = """
            INSERT INTO jugadores (id, nombre, posicion, equipo_id, foto_url)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """
        cursor.execute(
            sql_insert_jugador,
            (jugador_id, nombre, posicion, equipo_id, foto_url),
        )

    sql_upsert = """
        INSERT INTO puntos_jornada 
            (jugador_id, numero_jornada, puntos, minutos_jugados, goles, asistencias, tarjetas_amarillas, tarjetas_rojas)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (jugador_id, numero_jornada) DO UPDATE 
        SET puntos = EXCLUDED.puntos,
            minutos_jugados = EXCLUDED.minutos_jugados,
            goles = EXCLUDED.goles,
            asistencias = EXCLUDED.asistencias,
            tarjetas_amarillas = EXCLUDED.tarjetas_amarillas,
            tarjetas_rojas = EXCLUDED.tarjetas_rojas;
    """

    cursor.execute(
        sql_upsert,
        (
            jugador_id,
            numero_jornada,
            puntos_totales,
            stats.get("minutos", 0),
            stats.get("goles", 0),
            stats.get("asistencias", 0),
            stats.get("amarillas", 0),
            stats.get("rojas", 0),
        ),
    )

    conn.commit()
    cursor.close()
    conn.close()