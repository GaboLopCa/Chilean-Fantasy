from fastapi import APIRouter
from database import get_db_connection

router = APIRouter(prefix="/jugadores", tags=["Jugadores"])

@router.get("")
def listar_jugadores(posicion: str = None, limite: int = 50):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT j.id, j.nombre, j.posicion, j.precio, j.foto_url, e.nombre AS equipo 
            FROM jugadores j
            JOIN equipos e ON j.equipo_id = e.id
        """
        params = []

        if posicion:
            query += " WHERE j.posicion = %s"
            params.append(posicion)

        query += " LIMIT %s;"
        params.append(limite)

        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()