from fastapi import APIRouter
from database import get_db_connection

router = APIRouter(prefix="/ranking", tags=["Ranking"])

@router.get("")
def obtener_ranking():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT 
                u.id AS usuario_id,
                u.nombre_usuario,
                COALESCE(SUM(
                    CASE 
                        WHEN pu.es_capitan THEN COALESCE(pj.puntos, 0) * 2 
                        ELSE COALESCE(pj.puntos, 0) 
                    END
                ), 0) AS puntos_totales
            FROM usuarios u
            LEFT JOIN plantillas_usuarios pu ON u.id = pu.usuario_id
            LEFT JOIN puntos_jornada pj ON pu.jugador_id = pj.jugador_id
            GROUP BY u.id, u.nombre_usuario
            ORDER BY puntos_totales DESC;
        """
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()