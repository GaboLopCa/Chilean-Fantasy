from pydantic import BaseModel, EmailStr, Field

class UsuarioRegistro(BaseModel):
    nombre_usuario: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50)

class Token(BaseModel):
    access_token: str
    token_type: str
    usuario_id: str
    nombre_usuario: str

class AlineacionItem(BaseModel):
    jugador_id: int
    posicion_campo: str = Field(..., min_length=1, max_length=3)
    es_titular: bool = True

class GuardarAlineacionRequest(BaseModel):
    jugadores: list[AlineacionItem]

class ActualizarEstadoJornadaRequest(BaseModel):
    estado: str

class PujaRequest(BaseModel):
    jugador_id: int
    monto: int = Field(..., gt=0)

class PagarClausulaRequest(BaseModel):
    jugador_id: int

class AumentarClausulaRequest(BaseModel):
    jugador_id: int
    monto_incremento: int = Field(..., gt=0)

class ComprarAgenteRequest(BaseModel):
    jugador_id: int