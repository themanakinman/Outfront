# LA Street Parking AI Data Lakehouse

An autonomous, end-to-end data pipeline and Agentic RAG (Retrieval-Augmented Generation) application. This platform ingests live Los Angeles parking meter data, enriches it with geospatial inventory via Apache Iceberg, and provides a conversational AI interface using Google Gemini and BigQuery.

## Project Structure

This project is separated into four primary domains:

*   **`data_pipeline/`**: The core data engine.
    *   `ingestion/`: Python extraction scripts that fetch live occupancy and static inventory data from the LA SODA APIs, landing them as raw JSON in Google Cloud Storage (GCS).
    *   `processing/`: PySpark scripts that transform the raw JSON into ACID-compliant Apache Iceberg tables, performing a geospatial JOIN to create an enriched dataset.
*   **`ai_app/`**: The intelligence layer.
    *   `app_ai.py`: The conversational AI Agent using Gemini.
    *   `parking_tool.py`: The toolset provided to the LLM, handling geocoding (via OpenStreetMap) and BigQuery geospatial SQL execution.
*   **`k8s/`**: Kubernetes manifests deploying the pipeline to GKE Autopilot. Includes CronJobs that automate the hourly pull-and-merge process.
*   **`infrastructure/`**: IaC (Terraform) and BigQuery configurations. Manages the GCS Data Lake, GKE Cluster, and Workload Identity (IAM) security bindings.

## Architecture Overview

### 1. The Data Pipeline (ELT)
*   **Extract & Load (EL)**: Containerized Python scripts run on a GKE CronJob every hour, pulling 1,000+ live parking events and saving them as raw JSON in GCS.
*   **Transform (T)**: PySpark jobs run 5 minutes later on GKE, cleaning and merging the new data into an Iceberg table (`parking_catalog.db.occupancy`) for idempotent, reliable updates.
*   **Enrichment**: The Spark job subsequently joins the live occupancy data with a static geospatial inventory, producing an `enriched_occupancy` table containing exact coordinates for every meter.

### 2. The Data Lakehouse
*   **Storage**: GCS serves as the physical home for both raw data and processed Parquet files.
*   **Serving**: BigQuery acts as the query engine, utilizing an External Table to point directly to the Iceberg metadata in GCS. This exposes the data to SQL without duplicating storage.

### 3. Orchestration & Security
*   **Terraform**: Provisions the infrastructure and implements Workload Identity, allowing Kubernetes Service Accounts to securely access GCS without hardcoded keys.
*   **Kubernetes (GKE)**: Manages the automated pipeline. `ingest-cronjob.yaml` and `process-cronjob.yaml` run the extraction and Spark merging sequentially.

### 4. Agentic RAG Interface
*   **LLM Interface**: A Gemini AI Agent operates as the reasoning engine.
*   **Function Calling**: The Agent is equipped with Python tools. It parses natural language prompts to determine the best tool for the job.
*   **Geospatial Proximity**: When asked for parking near an address (e.g., "755 S Spring St"), the Agent geocodes the string into coordinates, injects them into a BigQuery `ST_DISTANCE` SQL statement, and returns the closest available parking spots to the user.

## How to Run the AI Assistant

1. Ensure your Python virtual environment is activated:
   ```zsh
   source venv/bin/activate
   ```
2. Navigate to the AI app folder:
   ```zsh
   cd ai_app
   ```
3. Run the chat interface:
   ```zsh
   python app_ai.py
   ```

*(Ensure your `.env` file containing `GOOGLE_API_KEY` is located in the root of the project or inside `ai_app/`)*

## Building the Docker Images

If modifying the data pipeline scripts, rebuild the images using the provided Dockerfiles in the root directory:

```zsh
# Build Ingestor
docker buildx build --platform linux/amd64 -f Dockerfile.ingest -t us-central1-docker.pkg.dev/ladot-496020/parking-repo/parking-ingest:v1 .

# Build Processor
docker buildx build --platform linux/amd64 -f Dockerfile.spark -t us-central1-docker.pkg.dev/ladot-496020/parking-repo/parking-processor:v1 .
```
