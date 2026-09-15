from fastapi import APIRouter, Depends
from database import get_db_connection
from routers.deps import get_current_user

router = APIRouter(prefix="/ranking", tags=["Ranking"])

@router.get("")
def obtener_ranking(_usuario_id: str = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT
                u.id AS usuario_id,
                u.nombre_usuario,
                COALESCE(SUM(COALESCE(pj.puntos, 0)), 0) AS puntos_totales
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