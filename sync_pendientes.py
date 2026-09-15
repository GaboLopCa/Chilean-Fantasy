# sync_pendientes.py
from sync_jornada import sincronizar_jornada


def sincronizar_partidos_pendientes():
    # Recorre de la fecha 1 a la fecha 30; solo procesará eventos con estado "finished"
    for jornada in range(1, 31):
        print(f"\n--- Procesando jornada {jornada} ---")
        sincronizar_jornada(numero_jornada=jornada)


if __name__ == "__main__":
    sincronizar_partidos_pendientes()