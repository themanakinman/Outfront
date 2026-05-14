# V1 Pipeline Completion Plan: SODA -> GCS -> Iceberg

## Current State
**Phase A: The Landing Zone (Completed)**
- The data producer (`ingest_parking.py`) has been successfully written and containerized.
- The `linux/amd64` architecture image is pushed to Google Artifact Registry.
- The Kubernetes Job (`ingest-job.yaml`) successfully utilizes the Workload Identity bridge (`spark-k8s-sa`) to authenticate securely without hardcoded keys.
- Raw JSON data from the LADOT SODA API is now successfully landing in the GCS bucket (`gs://parking-data-lake-ladot-496020/raw/`).

---

## Remaining Steps to Finish V1

The core objective of V1 is to establish the end-to-end flow from the API into a modern Data Lakehouse format (Apache Iceberg).

### Phase B: The Processing Engine (PySpark)
**Goal:** Move data from the `raw/` landing zone (JSON) to the `processed/` zone (Iceberg), applying schema enforcement and basic cleaning.

1. **Develop `process_parking.py` (The Spark Job):**
   - Initialize a `SparkSession` with Apache Iceberg extensions.
   - Define a strict schema for the incoming JSON data.
   - Read the raw JSON data from `gs://parking-data-lake-ladot-496020/raw/`.
   - Apply cleaning transformations: specifically, casting the `eventtime` string into a proper `TIMESTAMP`.
   - Write the resulting DataFrame out in `iceberg` format to the `processed/` bucket directory.

2. **Containerize the Spark Job:**
   - Create a `Dockerfile.spark` utilizing a base PySpark image.
   - Add necessary `.jar` dependencies for Iceberg and GCS connectors.
   - Build using `docker buildx` with `--platform linux/amd64`.
   - Push to Artifact Registry (e.g., `us-central1-docker.pkg.dev/ladot-496020/parking-repo/parking-processor:v1`).

3. **Deploy Spark on GKE:**
   - Create a `process-job.yaml` Kubernetes manifest.
   - Assign the exact same Workload Identity Service Account (`spark-k8s-sa`) used in ingestion so the job can read/write to the GCS bucket.
   - Deploy the job and verify successful data conversion via `kubectl logs`.

### Phase C: Orchestration (CronJobs)
**Goal:** Automate the pipeline so it runs continuously without manual intervention.

1. **Convert Jobs to CronJobs:**
   - Modify `ingest-job.yaml` to a `CronJob` resource, scheduled to run every 15 minutes.
   - Modify `process-job.yaml` to a `CronJob` running offset from the ingestion, or transition the Spark job to use **Structured Streaming** so it listens for new files continuously.

### Phase D: Validation & Preparation for V2
**Goal:** Ensure the Lakehouse is queryable and ready for the Enrichment Phase.

1. **Data Validation:** 
   - Use a lightweight query engine (like DuckDB or a local Spark shell) to query the new Iceberg table directly from GCS and verify the data looks correct.
2. **dbt Initialization:** 
   - Initialize a local `dbt` project using the `dbt-spark` adapter to prepare for V2 (where we will join this dynamic occupancy stream with static parking meter inventory locations).

---
## Summary of Pipeline Versions
* **V1 (Current Target):** SODA API -> GCS (JSON) -> PySpark -> Iceberg (Parquet).
* **V2 (Future):** Introduce dbt to join the dynamic `occupancy` stream with static `inventory` (Geo-locations).
* **V3 (Future):** Add an LLM/RAG vector search interface to query available parking via natural language.
