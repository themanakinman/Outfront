from pyspark.sql import SparkSession
from pyspark.sql.functions import col, get_json_object
import os
# pyrefly: ignore [missing-import]

BUCKET_NAME = os.getenv("BUCKET_NAME", "parking-data-lake-v1")
STATIC_PATH = f"gs://{BUCKET_NAME}/static/meter_inventory.json"
INV_TABLE = "parking_catalog.db.inventory"
OCC_TABLE = "parking_catalog.db.occupancy"
ENRICHED_TABLE = "parking_catalog.db.enriched_occupancy"

def main():
    spark = SparkSession.builder \
        .appName("InventoryProcessor") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.parking_catalog", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.parking_catalog.type", "hadoop") \
        .config("spark.sql.catalog.parking_catalog.warehouse", f"gs://{BUCKET_NAME}/processed") \
        .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem") \
        .config("spark.hadoop.fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS") \
        .getOrCreate()

    print(f"Processing inventory from {STATIC_PATH}...")

    # 1. Read and Clean Inventory
    df_inv = spark.read.json(STATIC_PATH)
    
    # The s49e-q6j2 dataset stores coordinates in a 'latlng' object with latitude/longitude fields
    df_inv_cleaned = df_inv.select(
        col("spaceid"),
        col("blockface"),
        col("latlng.latitude").alias("latitude"),
        col("latlng.longitude").alias("longitude")
    ).dropDuplicates(["spaceid"])

    # Save Inventory as a permanent Iceberg table
    df_inv_cleaned.write.format("iceberg").mode("overwrite").saveAsTable(INV_TABLE)
    print(f"Inventory table created: {INV_TABLE}")

    # 2. Perform the JOIN
    print("Joining Occupancy with Inventory...")
    df_occ = spark.table(OCC_TABLE)
    
    # Join on spaceid
    df_enriched = df_occ.join(df_inv_cleaned, "spaceid", "left")

    # 3. Save the Enriched Table
    # This is the table your LLM will eventually query!
    df_enriched.write.format("iceberg").mode("overwrite").saveAsTable(ENRICHED_TABLE)
    
    print(f"Enriched table created: {ENRICHED_TABLE}")
    print("Phase 2 Enrichment Complete.")

if __name__ == "__main__":
    main()
