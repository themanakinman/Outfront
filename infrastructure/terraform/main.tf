provider "google" {
  project = "ladot-496020"
  region  = "us-central1"
}

resource "google_storage_bucket" "data_lake" {
  name          = "parking-data-lake-v1"
  location      = "US"
  force_destroy = true
  uniform_bucket_level_access = true

  lifecycle_rule {
    action { type = "Delete" }
    condition { age = 30 }
  }
}

resource "google_container_cluster" "data_platform" {
  name     = "data-platform-cluster"
  location = "us-central1"
  enable_autopilot = true

  workload_identity_config {
    workload_pool = "ladot-496020.svc.id.goog"
  }
}

resource "google_service_account" "spark_sa" {
  account_id   = "spark-gcs-sa"
  display_name = "Service Account for Spark Workers"
}
resource "google_storage_bucket_iam_member" "bucket_access" {
  bucket = google_storage_bucket.data_lake.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.spark_sa.email}"
}

resource "google_service_account_iam_member" "workload_identity_binding" {
  service_account_id = google_service_account.spark_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:ladot-496020.svc.id.goog[default/spark-k8s-sa]"
}
