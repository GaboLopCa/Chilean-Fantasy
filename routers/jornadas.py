from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from database import get_db_connection
from schemas import ActualizarEstadoJornadaRequest
from routers.deps import get_current_user
from market_engine import actualizar_precios_jornada
import sync_jornada

router = APIRouter(prefix="/jornadas", tags=["Jornadas"])

@router.put("/{numero_jornada}/estado")
def cambiar_estado_jornada(
    numero_jornada: int,
    request: ActualizarEstadoJornadaRequest,
    _usuario_id: str = Depends(get_current_user),
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        nuevo_estado = request.estado.upper()

        if nuevo_estado not in ["ABIERTA", "EN_PROGRESO", "FINALIZADA"]:
            raise HTTPException(
                status_code=400,
                detail="Estado inválido. Use: ABIERTA, EN_PROGRESO o FINALIZADA."
            )

        # 1. Actualizar el estado de la jornada
        cursor.execute(
            "UPDATE jornadas SET estado = %s WHERE numero = %s RETURNING numero;",
            (nuevo_estado, numero_jornada)
        )
        jornada = cursor.fetchone()

        if not jornada:
            raise HTTPException(status_code=404, detail=f"No se encontró la jornada {numero_jornada}.")

        conn.commit()

        # 2. Si la jornada pasa a 'FINALIZADA', se dispara el ajuste automático de precios
        if nuevo_estado == "FINALIZADA":
            actualizar_precios_jornada(numero_jornada)

        return {
            "mensaje": f"Jornada {numero_jornada} actualizada a estado {nuevo_estado}.",
            "jornada_numero": numero_jornada,
            "estado": nuevo_estado
        }

    except HTTPException as he:
        conn.rollback()
        raise he
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar jornada: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.post("/{numero_jornada}/sincronizar")
def sincronizar_puntos_jornada(
    numero_jornada: int,
    _usuario_id: str = Depends(get_current_user),
):
    """Sincroniza y calcula puntos de la jornada desde SportAPI7, la marca
    FINALIZADA y ajusta los precios del mercado.

    NOTA ADMIN: el ranking y el mercado se alimentan de esta sincronización;
    si la jornada aún tiene partidos en juego, los pendientes se omiten.
    """
    try:
        sync_jornada.sincronizar_jornada(numero_jornada)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error al sincronizar la jornada {numero_jornada}: {str(e)}",
        )

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE jornadas SET estado = 'FINALIZADA' WHERE numero = %s RETURNING numero;",
            (numero_jornada,),
        )
        jornada = cursor.fetchone()
        if not jornada:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró la jornada {numero_jornada}.",
            )
        conn.commit()
    except HTTPException as he:
        conn.rollback()
        raise he
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al marcar la jornada finalizada: {str(e)}",
        )
    finally:
        cursor.close()
        conn.close()

    try:
        actualizar_precios_jornada(numero_jornada)
    except Exception as e:
        # La puntuación ya quedó registrada; el ajuste de precios es secundario.
        return JSONResponse(
            status_code=200,
            content={
                "mensaje": f"Jornada {numero_jornada} sincronizada y FINALIZADA. "
                          f"El ajuste de precios falló (secundario): {str(e)}",
                "jornada_numero": numero_jornada,
                "estado": "FINALIZADA",
            },
        )

    return {
        "mensaje": f"Jornada {numero_jornada} sincronizada, FINALIZADA y precios ajustados.",
        "jornada_numero": numero_jornada,
        "estado": "FINALIZADA",
    }