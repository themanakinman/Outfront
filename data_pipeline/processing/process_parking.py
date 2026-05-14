# pyrefly: ignore [missing-import]
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp
import os

BUCKET_NAME = os.getenv("BUCKET_NAME", "parking-data-lake-v1")
RAW_PATH = f"gs://{BUCKET_NAME}/raw/*.json"
TABLE_NAME = "parking_catalog.db.occupancy"

def main():
    spark = SparkSession.builder \
        .appName("ParkingDataProcessor") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.parking_catalog", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.parking_catalog.type", "hadoop") \
        .config("spark.sql.catalog.parking_catalog.warehouse", f"gs://{BUCKET_NAME}/processed") \
        .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem") \
        .config("spark.hadoop.fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS") \
        .getOrCreate()

    print(f"Reading raw data from {RAW_PATH}...")

    df_raw = spark.read.json(RAW_PATH)

    if df_raw.rdd.isEmpty():
        print("No data found in raw folder. Exiting.")
        return

    df_cleaned = df_raw.withColumn("event_timestamp", to_timestamp(col("eventtime"))) \
        .select(
            col("spaceid"),
            col("occupancystate"),
            col("event_timestamp")
        ) \
        .dropDuplicates(["spaceid", "event_timestamp"])

    print(f"Merging cleaned data into Iceberg table: {TABLE_NAME}")
    
    df_cleaned.createOrReplaceTempView("new_data")
    spark.sql(f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} USING iceberg AS SELECT * FROM new_data WHERE 1=0")

    spark.sql(f"""
        MERGE INTO {TABLE_NAME} t
        USING new_data s
        ON t.spaceid = s.spaceid AND t.event_timestamp = s.event_timestamp
        WHEN NOT MATCHED THEN INSERT *
    """)

    print("Processing complete.")

if __name__ == "__main__":
    main()
