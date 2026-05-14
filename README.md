# Outfront - LA Street Parking AI Data Lakehouse

![Outfront Demo](app_ui/src/assets/demo.gif)

An autonomous, end-to-end data pipeline and Agentic RAG (Retrieval-Augmented Generation) application. This platform ingests live Los Angeles parking meter data, enriches it with geospatial inventory via Apache Iceberg, and provides a beautiful, conversational React UI mapped to an AI backend using Google Gemini and BigQuery.

## Project Structure

This project is separated into four primary domains:

*   **`app_ui/`**: The modern React frontend interface.
    *   `src/App.jsx`: A responsive, split-screen UI that integrates MapLibre for Carto basemaps.
    *   `package.json`: Configured with `concurrently` to boot the entire stack (Frontend + AI Backend) simultaneously.
*   **`ai_app/`**: The intelligence layer and backend API.
    *   `app_ai.py`: A FastAPI server running the conversational AI Agent using Gemini.
    *   `parking_tool.py`: The toolset provided to the LLM, handling OpenStreetMap geocoding and BigQuery geospatial SQL execution.
*   **`data_pipeline/`**: The core data engine.
    *   `ingestion/`: Python extraction scripts that fetch live occupancy and static inventory data from the LA SODA APIs, landing them as raw JSON in Google Cloud Storage (GCS).
    *   `processing/`: PySpark scripts that transform the raw JSON into ACID-compliant Apache Iceberg tables.
*   **`k8s/` & `infrastructure/`**: IaC (Terraform) and Kubernetes manifests deploying the pipeline to GKE Autopilot. 

---

## Architecture Overview

### 1. The Data Lakehouse & Pipeline
*   **Extract & Load (EL)**: Containerized Python scripts run on a GKE CronJob every hour, pulling live parking events and saving them as raw JSON in GCS.
*   **Transform (T)**: PySpark jobs merge the data into an Iceberg table (`parking_catalog.db.occupancy`) for idempotent updates, then join the data with geospatial inventory to produce coordinates for every meter.
*   **Serving**: BigQuery acts as the query engine, utilizing an External Table to point directly to the Iceberg metadata in GCS.

### 2. Agentic RAG Interface
*   **FastAPI Backend**: The AI interface operates as a REST API endpoint serving parsed JSON directly to the frontend.
*   **LLM Intelligence**: A Gemini AI Agent operates as the reasoning engine, using Python tools to deduce exactly what SQL to run.
*   **Geospatial Proximity**: When asked for parking near an address (e.g., "755 S Spring St"), the Agent geocodes the string into coordinates, injects them into a BigQuery `ST_DISTANCE` SQL statement, and returns the closest available parking spots alongside an insightful chat response.

### 3. The Interactive UI
*   **Dynamic Map**: Once a user submits a query, a sleek split-pane interface slides into view. The top half renders a MapLibre component that dynamically drops FontAwesome car icons at the exact coordinates returned by the AI.
*   **Live Chat History**: The bottom half docks your text input and maintains a scrollable conversation history, allowing for fluid follow-up queries.

---

## How to Run the Application

Thanks to `concurrently`, spinning up the entire conversational AI experience requires just a single command.

1. Navigate to the frontend directory:
   ```zsh
   cd app_ui
   ```
2. Install dependencies (if you haven't already):
   ```zsh
   npm install
   ```
3. Start the entire stack:
   ```zsh
   npm run dev
   ```

*(This command will automatically boot the Vite React server on port 5173 AND launch the FastAPI Python server on port 8000. Ensure your `.env` file containing your `GOOGLE_API_KEY` is located in the root of the project.)*

---

## Building the Data Pipeline Docker Images

If you are modifying the data pipeline scripts (`ingestor.py` or `processor.py`) and need to update your GKE clusters, rebuild the images using the provided Dockerfiles:

```zsh
# Build Ingestor
docker buildx build --platform linux/amd64 -f Dockerfile.ingest -t us-central1-docker.pkg.dev/ladot-496020/parking-repo/parking-ingest:v1 .

# Build Processor
docker buildx build --platform linux/amd64 -f Dockerfile.spark -t us-central1-docker.pkg.dev/ladot-496020/parking-repo/parking-processor:v1 .
```
