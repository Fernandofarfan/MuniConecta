from app.models.schemas import validar_patente_argentina


class TestValidarPatente:
    def test_formato_viejo(self):
        assert validar_patente_argentina("AAA000") == "AAA000"

    def test_formato_nuevo(self):
        assert validar_patente_argentina("AB123CD") == "AB123CD"

    def test_formato_moto(self):
        assert validar_patente_argentina("123ABC") == "123ABC"

    def test_con_espacios(self):
        assert validar_patente_argentina(" AB 123 CD ") == "AB123CD"

    def test_con_guiones(self):
        assert validar_patente_argentina("AB-123-CD") == "AB123CD"

    def test_minusculas(self):
        assert validar_patente_argentina("ab123cd") == "AB123CD"

    def test_formato_invalido(self):
        try:
            validar_patente_argentina("XYZ12")
            raise AssertionError("Debio levantar ValueError")
        except ValueError:
            pass

    def test_formato_invalido_numeros_solos(self):
        try:
            validar_patente_argentina("12345")
            raise AssertionError("Debio levantar ValueError")
        except ValueError:
            pass

    def test_formato_invalido_vacio(self):
        try:
            validar_patente_argentina("")
            raise AssertionError("Debio levantar ValueError")
        except ValueError:
            pass
