FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias primero para cachear la capa
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código y los datos
COPY . .

# Exponer el puerto de la aplicación
EXPOSE 8080

# Iniciar Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
