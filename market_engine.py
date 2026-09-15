from database import get_raw_db_connection


def actualizar_precios_jornada(numero_jornada: int):
    """Ajusta precio y clausula de cada jugador según su rendimiento en la jornada."""
    conn = get_raw_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT jugador_id, puntos FROM puntos_jornada WHERE numero_jornada = %s;",
            (numero_jornada,),
        )
        registros = cursor.fetchall()

        for jugador_id, puntos in registros:
            # Incremento/decremento proporcional: 1% del precio por cada punto, tope ±10%
            porcentaje = max(min(puntos * 0.01, 0.10), -0.10)

            cursor.execute(
                """
                UPDATE jugadores
                SET precio = GREATEST(
                        ROUND(precio + precio * %s),
                        500000
                     ),
                    clausula = GREATEST(
                        ROUND(COALESCE(clausula, precio) + COALESCE(clausula, precio) * %s),
                        1000000
                     )
                WHERE id = %s;
                """,
                (porcentaje, porcentaje, jugador_id),
            )

        conn.commit()
        print(f"✅ Precios actualizados para {len(registros)} jugadores de la jornada {numero_jornada}.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error al actualizar precios: {e}")
    finally:
        cursor.close()
        conn.close()