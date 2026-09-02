# sync_pendientes.py (Lógica conceptual)
def sincronizar_partidos_pendientes():
    # Recorre de la fecha 1 a la fecha actual
    for jornada in range(1, 31):
        # Ejecuta la sincronización; solo procesará eventos con estado "finished"
        sincronizar_jornada(numero_jornada=jornada)