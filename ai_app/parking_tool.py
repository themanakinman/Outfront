from google.cloud import bigquery
import json

def query_parking(street_name: str = "", status: str = 'VACANT', limit: int = 5):
    """
    Searches for parking spots in Los Angeles.
    
    Args:
        street_name: The name of the street to search for (e.g., 'Main', 'Rose').
        status: The occupancy status to filter by ('VACANT' or 'OCCUPIED').
        limit: The maximum number of results to return.
    """
    client = bigquery.Client()
    
    # Base query
    sql = f"""
        SELECT spaceid, blockface, latitude, longitude, occupancystate
        FROM `parking_dw.enriched_parking`
        WHERE occupancystate = '{status}'
    """
    
    # Optional street filter
    if street_name:
        sql += f" AND UPPER(blockface) LIKE '%{street_name.upper()}%'"
        
    sql += f" LIMIT {limit}"
    
    query_job = client.query(sql)
    results = query_job.result()
    
    parking_spots = []
    for row in results:
        address = row.blockface if row.blockface else "Unknown Location"
        parking_spots.append({
            "spaceid": row.spaceid,
            "address": address,
            "coords": f"{row.latitude}, {row.longitude}",
            "status": row.occupancystate
        })
        
    return parking_spots

def get_unique_streets(limit: int = 20):
    """
    Returns a list of unique street names (blockfaces) available in the parking database.
    
    Args:
        limit: The maximum number of unique streets to return.
    """
    client = bigquery.Client()
    
    sql = f"""
        SELECT DISTINCT blockface 
        FROM `parking_dw.enriched_parking` 
        WHERE blockface IS NOT NULL
        ORDER BY blockface
        LIMIT {limit}
    """
    
    query_job = client.query(sql)
    results = query_job.result()
    
    streets = [row.blockface for row in results]
    return streets

import requests

def _geocode_address(address: str) -> tuple:
    """Helper function to convert an address to (lat, lon) using OpenStreetMap."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': f"{address}, Los Angeles, CA",
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'LAParkingAI/1.0'
    }
    try:
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code == 200 and len(resp.json()) > 0:
            data = resp.json()[0]
            return float(data['lat']), float(data['lon'])
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None, None

def find_parking_near_address(address: str, status: str = 'VACANT', limit: int = 5, radius_meters: int = 500):
    """
    Finds parking spots near a specific address using geospatial proximity search.
    
    Args:
        address: The address to search near (e.g., '755 S Spring St').
        status: The occupancy status ('VACANT' or 'OCCUPIED').
        limit: The maximum number of results to return.
        radius_meters: Maximum distance in meters to search within.
    """
    lat, lon = _geocode_address(address)
    
    if lat is None or lon is None:
        return {"error": f"Could not find coordinates for address: {address}. Try adding 'St' or 'Ave'."}
        
    client = bigquery.Client()
    
    # BigQuery uses ST_GEOGPOINT(longitude, latitude)
    sql = f"""
        SELECT 
            spaceid, 
            blockface, 
            latitude, 
            longitude, 
            occupancystate,
            ST_DISTANCE(
                ST_GEOGPOINT(longitude, latitude), 
                ST_GEOGPOINT({lon}, {lat})
            ) as distance_meters
        FROM `parking_dw.enriched_parking`
        WHERE occupancystate = '{status}'
          AND latitude IS NOT NULL 
          AND longitude IS NOT NULL
          AND ST_DWithin(
                ST_GEOGPOINT(longitude, latitude), 
                ST_GEOGPOINT({lon}, {lat}), 
                {radius_meters}
          )
        ORDER BY distance_meters ASC
        LIMIT {limit}
    """
    
    query_job = client.query(sql)
    results = query_job.result()
    
    parking_spots = []
    for row in results:
        parking_spots.append({
            "spaceid": row.spaceid,
            "address": row.blockface if row.blockface else "Unknown",
            "distance_meters": round(row.distance_meters, 1),
            "status": row.occupancystate
        })
        
    return parking_spots

if __name__ == "__main__":
    print("Testing 'Main St' search...")
    print(json.dumps(query_parking(street_name="MAIN"), indent=2))
    print("\nTesting 'get_unique_streets'...")
    print(get_unique_streets(limit=5))
