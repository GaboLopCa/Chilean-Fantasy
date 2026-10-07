from fastapi import HTTPException


def validar_reglas_plantilla(cursor, titulares: list[dict]):
    """Valida las reglas fantasy de la alineación TITULAR (11 jugadores).

    Recibe los titulares como [{"jugador_id": int, "posicion_campo": str}, ...].

    Reglas:
    1. Lineup Lock: la jornada activa (menor número no finalizada) debe estar ABIERTA.
    2. Cantidad: exactamente 11 titulares.
    3. Existencia: los 11 IDs deben existir en la BD (sin duplicados).
    4. Formación: 1G, 3-5D, 3-5M, 1-3F según el `posicion_campo` declarado.
    5. Límite por equipo: máximo 5 jugadores del mismo club.

    No valida saldo: comprar ya descontó el costo; re-alinear no gasta dinero.
    """
    if len(titulares) != 11:
        raise HTTPException(
            status_code=400,
            detail="Debes alinear exactamente 11 titulares.",
        )

    jugador_ids = [t["jugador_id"] for t in titulares]
    if len(set(jugador_ids)) != 11:
        raise HTTPException(
            status_code=400,
            detail="Hay jugadores duplicados en la alineación.",
        )

    # 1. Lineup Lock: la jornada activa debe estar ABIERTA
    cursor.execute(
        """
        SELECT numero, estado FROM jornadas
        WHERE estado != 'FINALIZADA'
        ORDER BY numero ASC LIMIT 1;
        """
    )
    jornada_activa = cursor.fetchone()

    if not jornada_activa:
        raise HTTPException(
            status_code=400,
            detail="Lineup Lock: no quedan jornadas abiertas en la temporada. "
                   "No se admiten cambios de alineación.",
        )

    if jornada_activa["estado"] != "ABIERTA":
        raise HTTPException(
            status_code=400,
            detail=f"Lineup Lock: la jornada {jornada_activa['numero']} está "
                   f"{jornada_activa['estado']}; no puedes modificar tu alineación.",
        )

    # 3. Existencia de los 11 jugadores
    cursor.execute(
        "SELECT id, equipo_id FROM jugadores WHERE id = ANY(%s);",
        (jugador_ids,),
    )
    filas = cursor.fetchall()

    if len(filas) != 11:
        raise HTTPException(
            status_code=400,
            detail="Uno o más jugadores seleccionados no existen en la base de datos.",
        )

    # 4. Formación según la posición en campo declarada
    posiciones = [t["posicion_campo"] for t in titulares]
    gk_count = posiciones.count("G")
    def_count = posiciones.count("D")
    mid_count = posiciones.count("M")
    att_count = posiciones.count("F")

    if gk_count != 1:
        raise HTTPException(
            status_code=400,
            detail="Debes alinear exactamente 1 Guardameta (G).",
        )
    if not (3 <= def_count <= 5):
        raise HTTPException(
            status_code=400,
            detail="Debes alinear entre 3 y 5 Defensores (D).",
        )
    if not (3 <= mid_count <= 5):
        raise HTTPException(
            status_code=400,
            detail="Debes alinear entre 3 y 5 Mediocampistas (M).",
        )
    if not (1 <= att_count <= 3):
        raise HTTPException(
            status_code=400,
            detail="Debes alinear entre 1 y 3 Delanteros (F).",
        )

    # 5. Límite de 5 jugadores por club (según el club real del jugador)
    equipos_count = {}
    for fila in filas:
        eq = fila["equipo_id"]
        equipos_count[eq] = equipos_count.get(eq, 0) + 1
        if equipos_count[eq] > 5:
            raise HTTPException(
                status_code=400,
                detail="No puedes alinear más de 5 jugadores del mismo club.",
            )
