provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "telegram_bot_token" {
  description = "Telegram Bot Token"
  type        = string
  sensitive   = true
}

variable "gemini_api_key" {
  description = "Gemini API Key"
  type        = string
  sensitive   = true
}

resource "google_cloud_run_v2_service" "municonecta_service" {
  name     = "municonecta-service"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      # Reemplazar con la imagen de tu contenedor Docker subido a Artifact Registry
      image = "us-docker.pkg.dev/cloudrun/container/hello" 
      
      env {
        name  = "TELEGRAM_BOT_TOKEN"
        value = var.telegram_bot_token
      }
      env {
        name  = "GEMINI_API_KEY"
        value = var.gemini_api_key
      }
    }
  }
}

# Permite acceso público no autenticado para recibir los webhooks de Telegram
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.municonecta_service.location
  project  = google_cloud_run_v2_service.municonecta_service.project
  service  = google_cloud_run_v2_service.municonecta_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
