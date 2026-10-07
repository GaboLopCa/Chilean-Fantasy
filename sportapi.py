import os
import time
import requests
from dotenv import load_dotenv
from database import get_raw_db_connection

load_dotenv()

TOURNAMENT_ID = 11653
BASE_URL = "https://sportapi7.p.rapidapi.com/api/v1"

HEADERS = {
    "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
    "x-rapidapi-host": os.getenv("RAPIDAPI_HOST"),
}


class ApiError(Exception):
    pass


class CuotaAgotada(ApiError):
    pass


def api_get(path: str, params: dict = None, timeout: int = 20):
    """GET a SportAPI7 con manejo de errores estandarizado.

    - 200  -> devuelve el JSON
    - 429  -> CuotaAgotada (plan mensual superado, no reintenta)
    - 5xx  -> ApiError descriptivo
    - Timeout/ConnectionError -> 1 reintento con backoff (no consume cuota)
    """
    url = f"{BASE_URL}{path}"

    for intento in range(2):
        try:
            respuesta = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
        except (requests.ConnectionError, requests.Timeout) as e:
            if intento == 0:
                time.sleep(1)
                continue
            raise ApiError(f"Error de red al consultar {url}: {e}")

        if respuesta.status_code == 200:
            return respuesta.json()

        if respuesta.status_code == 429:
            raise CuotaAgotada(
                f"Cuota mensual de SportAPI7 agotada (HTTP 429). "
                f"Espera la renovación del plan Basic o sube de plan."
            )

        raise ApiError(f"SportAPI7 respondió {respuesta.status_code} en {path}: {respuesta.text[:200]}")

    raise ApiError(f"Falló la petición a {url} tras los reintentos.")


# ---------------------------------------------------------------------------
# Caché de metadatos en BD (evita re-consultar /seasons en cada corrida)
# ---------------------------------------------------------------------------

def asegurar_tablas_sync():
    conn = get_raw_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metadatos (
                clave          text PRIMARY KEY,
                valor          text NOT NULL,
                actualizado_en timestamptz NOT NULL DEFAULT now()
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS eventos_sincronizados (
                event_id        bigint PRIMARY KEY,
                numero_jornada  integer NOT NULL,
                sincronizado_en timestamptz NOT NULL DEFAULT now()
            );
            """
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_metadato(clave: str):
    conn = get_raw_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT valor FROM metadatos WHERE clave = %s;", (clave,))
        fila = cursor.fetchone()
        return fila[0] if fila else None
    finally:
        cursor.close()
        conn.close()


def set_metadato(clave: str, valor: str):
    conn = get_raw_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO metadatos (clave, valor)
            VALUES (%s, %s)
            ON CONFLICT (clave) DO UPDATE
            SET valor = EXCLUDED.valor, actualizado_en = now();
            """,
            (clave, valor),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def obtener_season_actual() -> tuple[int, str]:
    """Devuelve (season_id, season_name) usando la caché de BD cuando existe.

    Solo consume 1 request de /seasons si no hay valor cacheado (primera vez).
    """
    asegurar_tablas_sync()

    cached_id = get_metadato("season_id")
    cached_name = get_metadato("season_name")

    if cached_id and cached_name:
        return int(cached_id), cached_name

    data = api_get(f"/unique-tournament/{TOURNAMENT_ID}/seasons")
    season = data["seasons"][0]
    season_id, season_name = season["id"], season["name"]

    set_metadato("season_id", str(season_id))
    set_metadato("season_name", season_name)
    return int(season_id), season_name