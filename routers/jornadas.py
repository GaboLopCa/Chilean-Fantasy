from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from database import get_db_connection
from schemas import ActualizarEstadoJornadaRequest
from routers.deps import get_current_user
from market_engine import actualizar_precios_jornada
from sportapi import CuotaAgotada
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

        cursor.execute(
            "UPDATE jornadas SET estado = %s WHERE numero = %s RETURNING numero;",
            (nuevo_estado, numero_jornada)
        )
        jornada = cursor.fetchone()

        if not jornada:
            raise HTTPException(status_code=404, detail=f"No se encontró la jornada {numero_jornada}.")

        conn.commit()

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
    """Sincroniza y calcula puntos de la jornada desde SportAPI7.

    - Pasa a FINALIZADA (y ajusta precios) SOLO si todos los partidos de la
      fecha terminaron; si quedan pendientes, queda en EN_PROGRESO y se puede
      re-invocar sin costo para los eventos ya importados.
    """
    try:
        resumen = sync_jornada.sincronizar_jornada(numero_jornada)
    except CuotaAgotada as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error al sincronizar la jornada {numero_jornada}: {str(e)}",
        )

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if resumen["partidos_pendientes"] == 0 and resumen["partidos_total"] > 0:
            nuevo_estado = "FINALIZADA"
        elif resumen["partidos_total"] > 0:
            nuevo_estado = "EN_PROGRESO"
        else:
            nuevo_estado = "ABIERTA"

        cursor.execute(
            """
            INSERT INTO jornadas (numero, estado)
            VALUES (%s, %s)
            ON CONFLICT (numero) DO UPDATE SET estado = EXCLUDED.estado
            RETURNING numero;
            """,
            (numero_jornada, nuevo_estado),
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar la jornada: {str(e)}",
        )
    finally:
        cursor.close()
        conn.close()

    mensaje = f"Jornada {numero_jornada} sincronizada."

    if nuevo_estado == "FINALIZADA":
        try:
            actualizar_precios_jornada(numero_jornada)
        except Exception as e:
            return JSONResponse(
                status_code=200,
                content={
                    "mensaje": f"{mensaje} Marcada FINALIZADA. "
                               f"El ajuste de precios falló (secundario): {str(e)}",
                    "jornada_numero": numero_jornada,
                    "estado": nuevo_estado,
                    "resumen": resumen,
                },
            )
        mensaje += " FINALIZADA y precios ajustados."
    elif nuevo_estado == "EN_PROGRESO":
        mensaje += (
            f" Quedan {resumen['partidos_pendientes']} partidos sin terminar; "
            f"está en EN_PROGRESO. Re-invócala cuando terminen (no re-gasta "
            f"requests en los eventos ya importados)."
        )
    else:
        mensaje += " Sin partidos registrados; queda ABIERTA."

    return {
        "mensaje": mensaje,
        "jornada_numero": numero_jornada,
        "estado": nuevo_estado,
        "resumen": resumen,
    }