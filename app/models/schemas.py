import re

from pydantic import BaseModel, field_validator

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
    raise ValueError("Formato de patente argentina no valido. Ejemplos: AB123CD, AB123CD, 123ABC")


class PeticionIniciarEstacionamiento(BaseModel):
    patente: str
    tipo_vehiculo: str
    legajo_permisionario: str

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
