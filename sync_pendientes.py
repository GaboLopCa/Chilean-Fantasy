import argparse
import sys
from database import get_raw_db_connection
from sync_jornada import sincronizar_jornada
from sportapi import asegurar_tablas_sync


def jornadas_finalizadas() -> set[int]:
    conn = get_raw_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT numero FROM jornadas WHERE estado = 'FINALIZADA';"
        )
        return {row[0] for row in cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


def sincronizar_partidos_pendientes(desde: int = 1, hasta: int = 30):
    """Recorre un rango de fechas sincronizando solo las no finalizadas.

    Respeta la cuota del plan Basic: cada fecha ya marcada FINALIZADA se
    omite sin gastar un solo request.
    """
    finalizadas = jornadas_finalizadas()

    for jornada in range(desde, hasta + 1):
        if jornada in finalizadas:
            print(f"--- Jornada {jornada}: ya FINALIZADA, se omite (0 requests). ---")
            continue

        print(f"\n--- Procesando jornada {jornada} ---")
        sincronizar_jornada(numero_jornada=jornada)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sincroniza jornadas pendientes de la API."
    )
    parser.add_argument("--desde", type=int, default=1, help="Primera jornada (default 1)")
    parser.add_argument("--hasta", type=int, default=30, help="Última jornada (default 30)")
    args = parser.parse_args()

    asegurar_tablas_sync()
    sincronizar_partidos_pendientes(desde=args.desde, hasta=args.hasta)
    sys.exit()