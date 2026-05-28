# MuniConecta - Guía de Despliegue y Pruebas

Este documento detalla los pasos exactos para probar la aplicación localmente en tiempo real y para preparar, construir y desplegar MuniConecta en Google Cloud Platform (GCP) utilizando Docker, Artifact Registry y Terraform.

## Desarrollo y Pruebas Locales (Modo Polling)

Si quieres probar el bot localmente en tiempo real sin desplegarlo en Google Cloud Platform, puedes hacerlo utilizando el script de Polling local. Esto leerá las actualizaciones directamente desde la API de Telegram sin necesidad de configurar Webhooks ni HTTPS locales.

### 1. Configurar el archivo `.env`
Asegúrate de tener un archivo `.env` en la raíz del proyecto con las siguientes variables:
```env
TELEGRAM_BOT_TOKEN=tu_token_de_telegram
GEMINI_API_KEY=tu_api_key_de_gemini
```

### 2. Ejecutar el bot localmente
Ejecuta el script `local_poll.py` utilizando tu entorno virtual:

**En Windows:**
```powershell
.\venv\Scripts\python.exe local_poll.py
```

**En Linux/macOS:**
```bash
source venv/bin/activate
python local_poll.py
```

*Nota: Este script borrará temporalmente cualquier Webhook configurado en Telegram para que las actualizaciones se reciban directamente en tu máquina.*

---

## Despliegue en GCP (Producción)

## Requisitos Previos

- Tener instalados: `gcloud` CLI, `docker`, y `terraform`.
- Tener un proyecto en GCP creado (reemplazar `<TU_PROJECT_ID>` por el ID real en los comandos).

## 1. Autenticación y Configuración de GCP

Primero, inicia sesión y configura tu proyecto por defecto:

```bash
gcloud auth login
gcloud config set project <TU_PROJECT_ID>
gcloud auth configure-docker us-central1-docker.pkg.dev
```

*(Asegúrate de tener habilitada la API de Artifact Registry y Cloud Run en tu proyecto).*

## 2. Construir y Subir la Imagen Docker

Construye la imagen de FastAPI localmente y haz push al repositorio de Artifact Registry:

```bash
# Construir la imagen
docker build -t us-central1-docker.pkg.dev/283983142913/municonecta-repo/municonecta-api:latest .

# Subir la imagen a Artifact Registry
docker push us-central1-docker.pkg.dev/283983142913/municonecta-repo/municonecta-api:latest
```

## 3. Desplegar Infraestructura con Terraform

Inicializa Terraform y aplica los cambios. Se te pedirán las variables sensibles o puedes pasarlas directamente en el comando:

```bash
terraform init

terraform apply \
  -var="project_id=<TU_PROJECT_ID>" \
  -var="telegram_bot_token=<TU_TELEGRAM_BOT_TOKEN>" \
  -var="gemini_api_key=<TU_GEMINI_API_KEY>" \
  -var="docker_image=us-central1-docker.pkg.dev/283983142913/municonecta-repo/municonecta-api:latest"
```

Confirma la acción escribiendo `yes` cuando Terraform te lo solicite. Al finalizar, Terraform mostrará el output `cloud_run_url`.

## 4. Configurar el Webhook de Telegram

Copia la URL que devolvió Terraform (el `cloud_run_url`) y ejecuta el siguiente comando para conectar el bot de Telegram con el endpoint de tu API en Cloud Run:

```bash
curl -F "url=<URL_DE_CLOUD_RUN>/webhook" https://api.telegram.org/bot<TU_TELEGRAM_BOT_TOKEN>/setWebhook
```
*(Nota: Asegúrate de reemplazar `<URL_DE_CLOUD_RUN>` y `<TU_TELEGRAM_BOT_TOKEN>` con tus valores reales. Además, el endpoint exacto debe coincidir con la ruta definida en tu FastAPI, por ejemplo `/webhook` si esa es tu ruta POST).*
