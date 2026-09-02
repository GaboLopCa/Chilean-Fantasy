from fastapi import APIRouter, HTTPException
# Importa tu conexión a la base de datos (por ejemplo, get_db_connection, db, o psycopg2)
from database import get_db_connection  # <--- Asegúrate de importar tu función de conexión

router = APIRouter(prefix="/plantilla", tags=["Plantillas"])

@router.get("/{usuario_id}")
def obtener_plantilla(usuario_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()  # <--- AQUÍ SE DEFINE EL CURSOR
    
    try:
        # Asegúrate de usar 'equipo_id' o el JOIN correspondiente según la BD
        cursor.execute(
            """
            SELECT id, nombre, posicion, equipo_id, clausula 
            FROM jugadores 
            WHERE propietario_id = %s
            """,
            (usuario_id,)
        )
        
        # Si estás usando RealDictCursor o recuperando tuplas:
        columnas = [desc[0] for desc in cursor.description]
        jugadores = [dict(zip(columnas, row)) for row in cursor.fetchall()]
        
        return {"jugadores": jugadores}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Siempre cierra el cursor y la conexión
        cursor.close()
        conn.close()