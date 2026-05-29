import re

from pydantic import BaseModel, Field, field_validator

PATENTE_VIEJA_RE = re.compile(r"^[A-Z]{3}\d{3}$")
PATENTE_NUEVA_RE = re.compile(r"^[A-Z]{2}\d{3}[A-Z]{2}$")
PATENTE_MOTO_RE = re.compile(r"^\d{3}[A-Z]{3}$")


def validar_patente_argentina(patente: str) -> str:
    patente = patente.upper().strip().replace(" ", "").replace("-", "")
    if PATENTE_VIEJA_RE.match(patente):
        return patente
    if PATENTE_NUEVA_RE.match(patente):
        return patente
    if PATENTE_MOTO_RE.match(patente):
        return patente
    raise ValueError("Formato de patente argentina no valido. Ejemplos: AAA000, AB123CD, 123ABC")


# --- Estacionamiento ---

class PeticionIniciarEstacionamiento(BaseModel):
    patente: str
    tipo_vehiculo: str
    legajo_permisionario: str
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    zona_id: int | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "patente": "AB123CD",
                "tipo_vehiculo": "auto",
                "legajo_permisionario": "INSP-01",
                "lat": -24.7883,
                "lon": -65.4105,
                "zona_id": 1,
            }]
        }
    }

    @field_validator("patente")
    @classmethod
    def patente_valida(cls, v: str) -> str:
        return validar_patente_argentina(v)

    @field_validator("tipo_vehiculo")
    @classmethod
    def tipo_vehiculo_valido(cls, v: str) -> str:
        if v not in ("auto", "moto"):
            raise ValueError("El tipo de vehiculo debe ser 'auto' o 'moto'")
        return v

    @field_validator("legajo_permisionario")
    @classmethod
    def legajo_valido(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El legajo del permisionario es obligatorio")
        return v.strip()


class PeticionCalcularCobro(BaseModel):
    patente: str
    metodo_pago: str

    @field_validator("patente")
    @classmethod
    def patente_valida(cls, v: str) -> str:
        return validar_patente_argentina(v)

    @field_validator("metodo_pago")
    @classmethod
    def metodo_pago_valido(cls, v: str) -> str:
        if v not in ("digital", "efectivo"):
            raise ValueError("El metodo de pago debe ser 'digital' o 'efectivo'")
        return v


class PeticionConsultaDeuda(BaseModel):
    patente: str

    @field_validator("patente")
    @classmethod
    def patente_valida(cls, v: str) -> str:
        return validar_patente_argentina(v)


class PeticionOCR(BaseModel):
    imagen_base64: str


# --- Auth ---

class PeticionLogin(BaseModel):
    legajo: str
    password: str


class RespuestaLogin(BaseModel):
    access_token: str
    token_type: str = "bearer"
    inspector: dict


# --- Zonas ---

class PeticionCrearZona(BaseModel):
    nombre: str
    tarifa_auto: int = 700
    tarifa_moto: int = 300
    capacidad_maxima: int = 50
    activa: bool = True


# --- Pagos ---

class PeticionCrearPago(BaseModel):
    patente: str
    email: str | None = "cliente@email.com"

    @field_validator("patente")
    @classmethod
    def patente_valida(cls, v: str) -> str:
        return validar_patente_argentina(v)


# --- Ciudadanos ---

class PeticionRegistrarCiudadano(BaseModel):
    telegram_chat_id: int
    nombre: str
    patentes: list[str]

    @field_validator("patentes")
    @classmethod
    def validar_patentes(cls, v: list[str]) -> list[str]:
        return [validar_patente_argentina(p) for p in v]


# --- Analiticas ---

class PeticionAnaliticas(BaseModel):
    desde: str
    hasta: str
    agrupacion: str = "dia"
