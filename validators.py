from fastapi import HTTPException

def validar_reglas_plantilla(cursor, jugador_ids: list[int], usuario_id: str):
    cursor.execute(
        "SELECT numero, estado FROM jornadas WHERE estado = 'ABIERTA' ORDER BY numero ASC LIMIT 1;"
    )
    jornada_activa = cursor.fetchone()

    if not jornada_activa:
        raise HTTPException(
            status_code=400,
            detail="La alineación se encuentra bloqueada (Lineup Lock). No hay jornadas abiertas para cambios.",
        )

    query = """
        SELECT id, posicion, precio, equipo_id 
        FROM jugadores 
        WHERE id = ANY(%s);
    """
    cursor.execute(query, (jugador_ids,))
    jugadores = cursor.fetchall()

    if len(jugadores) != 11:
        raise HTTPException(
            status_code=400,
            detail="Uno o más jugadores seleccionados no existen en la base de datos.",
        )

    cursor.execute(
        "SELECT presupuesto FROM usuarios WHERE id = %s;", (usuario_id,)
    )
    usuario = cursor.fetchone()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    costo_total = sum(j["precio"] for j in jugadores)
    if costo_total > usuario["presupuesto"]:
        raise HTTPException(
            status_code=400,
            detail=f"Superas el presupuesto permitido. Costo: ${costo_total:,.0f} | Límite: ${usuario['presupuesto']:,.0f}",
        )

    posiciones = [j["posicion"] for j in jugadores]
    gk_count = posiciones.count("G")
    def_count = posiciones.count("D")
    mid_count = posiciones.count("M")
    att_count = posiciones.count("F")

    if gk_count != 1:
        raise HTTPException(status_code=400, detail="Debes incluir exactamente 1 Guardameta (G).")
    if not (3 <= def_count <= 5):
        raise HTTPException(status_code=400, detail="Debes alinear entre 3 y 5 Defensores (D).")
    if not (3 <= mid_count <= 5):
        raise HTTPException(status_code=400, detail="Debes alinear entre 3 y 5 Mediocampistas (M).")
    if not (1 <= att_count <= 3):
        raise HTTPException(status_code=400, detail="Debes alinear entre 1 y 3 Delanteros (F).")

    equipos_count = {}
    for j in jugadores:
        eq = j["equipo_id"]
        equipos_count[eq] = equipos_count.get(eq, 0) + 1
        if equipos_count[eq] > 5:
            raise HTTPException(
                status_code=400,
                detail="No puedes seleccionar más de 5 jugadores del mismo club.",
            )