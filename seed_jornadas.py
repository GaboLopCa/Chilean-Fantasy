import argparse
import os
from dotenv import load_dotenv
from database import get_raw_db_connection

load_dotenv()

TOTAL_JORNADAS = 30


def sembrar_jornadas(desde: int = 1, hasta: int = TOTAL_JORNADAS):
    conn = get_raw_db_connection()
    cursor = conn.cursor()
    creadas = 0
    for n in range(desde, hasta + 1):
        cursor.execute(
            "INSERT INTO jornadas (numero) VALUES (%s) ON CONFLICT (numero) DO NOTHING;",
            (n,),
        )
        if cursor.rowcount > 0:
            creadas += 1
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Jornadas sembradas: {creadas} nuevas (rango {desde}..{hasta}).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Poblado de la tabla jornadas.")
    parser.add_argument("--desde", type=int, default=1)
    parser.add_argument("--hasta", type=int, default=TOTAL_JORNADAS)
    args = parser.parse_args()
    sembrar_jornadas(desde=args.desde, hasta=args.hasta)