from fastapi import APIRouter, Depends, HTTPException
from database import get_db_connection
from schemas import GuardarAlineacionRequest
from routers.deps import get_current_user

router = APIRouter(prefix="/plantilla", tags=["Plantillas"])

POSICIONES_VALIDAS = {"G", "D", "M", "F"}


@router.get("/{usuario_id}")
def obtener_plantilla(
    usuario_id: str,
    current_user_id: str = Depends(get_current_user),
):
    if usuario_id != current_user_id:
        raise HTTPException(status_code=403, detail="No puedes ver la plantilla de otro usuario.")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT j.id, j.nombre, j.posicion, j.equipo_id, j.clausula,
                   COALESCE(pu.posicion_campo, j.posicion) AS posicion_campo,
                   COALESCE(pu.es_titular, true) AS es_titular
            FROM jugadores j
            LEFT JOIN plantillas_usuarios pu
                ON pu.jugador_id = j.id AND pu.usuario_id = j.propietario_id
            WHERE j.propietario_id = %s
            ORDER BY
                CASE COALESCE(pu.posicion_campo, j.posicion)
                    WHEN 'G' THEN 1
                    WHEN 'D' THEN 2
                    WHEN 'M' THEN 3
                    WHEN 'F' THEN 4
                    ELSE 5
                END,
                j.nombre
            """,
            (usuario_id,)
        )

        return {"jugadores": cursor.fetchall()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


@router.put("/{usuario_id}")
def guardar_alineacion(
    usuario_id: str,
    payload: GuardarAlineacionRequest,
    current_user_id: str = Depends(get_current_user),
):
    if usuario_id != current_user_id:
        raise HTTPException(status_code=403, detail="No puedes modificar la plantilla de otro usuario.")

    titulares = [p for p in payload.jugadores if p.es_titular]
    if len(titulares) > 11:
        raise HTTPException(status_code=400, detail="Máximo 11 titulares en la alineación.")

    posiciones_erroneas = {
        p.jugador_id
        for p in payload.jugadores
        if p.posicion_campo not in POSICIONES_VALIDAS
    }
    if posiciones_erroneas:
        raise HTTPException(
            status_code=400,
            detail=f"Posiciones inválidas para jugador(es) {sorted(posiciones_erroneas)}. Usa G, D, M o F.",
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id FROM jugadores WHERE propietario_id = %s",
            (usuario_id,)
        )
        mis_jugadores = {row["id"] for row in cursor.fetchall()}

        ids_recibidos = {p.jugador_id for p in payload.jugadores}
        ids_ajenos = ids_recibidos - mis_jugadores
        if ids_ajenos:
            raise HTTPException(
                status_code=400,
                detail=f"No puedes alinear jugadores que no son tuyos: {sorted(ids_ajenos)}",
            )

        # Reemplaza la alineación previa del usuario (si existe)
        cursor.execute("DELETE FROM plantillas_usuarios WHERE usuario_id = %s", (usuario_id,))

        for item in payload.jugadores:
            cursor.execute(
                """
                INSERT INTO plantillas_usuarios (usuario_id, jugador_id, es_titular, posicion_campo)
                VALUES (%s, %s, %s, %s)
                """,
                (usuario_id, item.jugador_id, item.es_titular, item.posicion_campo),
            )

        conn.commit()
        return {
            "mensaje": "Alineación guardada.",
            "titulares": len(titulares),
            "banca": len(payload.jugadores) - len(titulares),
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()