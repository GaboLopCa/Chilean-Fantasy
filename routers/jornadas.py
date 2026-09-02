from fastapi import APIRouter, HTTPException, status
from database import get_db_connection
from schemas import ActualizarEstadoJornadaRequest
from market_engine import actualizar_precios_jornada  # <-- Importamos la función de la economía

router = APIRouter(prefix="/jornadas", tags=["Jornadas"])

@router.put("/{numero_jornada}/estado")
def cambiar_estado_jornada(numero_jornada: int, request: ActualizarEstadoJornadaRequest):
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
            "UPDATE jornadas SET estado = %s WHERE numero = %s RETURNING id;",
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