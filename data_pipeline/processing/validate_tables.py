from pyspark.sql import SparkSession
import os

BUCKET_NAME = os.getenv("BUCKET_NAME", "parking-data-lake-v1")
ENRICHED_TABLE = "parking_catalog.db.enriched_occupancy"

def main():
    spark = SparkSession.builder \
        .appName("DataValidator") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.parking_catalog", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.parking_catalog.type", "hadoop") \
        .config("spark.sql.catalog.parking_catalog.warehouse", f"gs://{BUCKET_NAME}/processed") \
        .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem") \
        .config("spark.hadoop.fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS") \
        .getOrCreate()

    print(f"--- VALIDATING TABLE: {ENRICHED_TABLE} ---")
    
    try:
        df = spark.table(ENRICHED_TABLE)
        
        print("\n[1] Table Schema:")
        df.printSchema()
        
        print("\n[2] Sample Data (First 10 rows):")
        df.show(10, truncate=False)
        
        count_all = df.count()
        count_joined = df.filter("latitude IS NOT NULL").count()
        
        print(f"\n[3] Stats:")
        print(f"Total Occupancy Records: {count_all}")
        print(f"Successfully Joined with Inventory: {count_joined}")
        
        if count_joined > 0:
            print("\n✅ SUCCESS: The join was successful!")
        else:
            print("\n❌ WARNING: No records were joined. Check SpaceID formats.")
            
    except Exception as e:
        print(f"Error reading table: {e}")

if __name__ == "__main__":
    main()
