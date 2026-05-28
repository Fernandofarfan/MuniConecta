from fastapi.testclient import TestClient
from main import app

cliente = TestClient(app)

def test_validacion_vehiculo_invalido():
    respuesta = cliente.post("/iniciar_estacionamiento", json={
        "patente": "AB123CD",
        "tipo_vehiculo": "camion", 
        "legajo_permisionario": "INSP-01"
    })
    assert respuesta.status_code == 400

def test_mock_ocr():
    respuesta = cliente.post("/escanear_patente", json={"imagen_base64": "datos_falsos"})
    assert respuesta.status_code == 200
    assert "patente_detectada" in respuesta.json()
