import sqlite3
import sys
from contextlib import closing
import requests
from tabulate import tabulate

API_URL = "https://api.open-meteo.com/v1/forecast?latitude=19.07&longitude=72.88&current_weather=true&hourly=temperature_2m,relativehumidity_2m,windspeed_10m"
DB_NAME = "weather.db"
TABLE_NAME = "weather_data"

def fetch_weather_data(url: str) -> dict:
    """Fetches weather data from the API and returns the parsed JSON response."""
    print("Fetching weather data from Open-Meteo API...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Network error occurred while fetching weather data: {e}", file=sys.stderr)
        raise
    except ValueError as e:
        print(f"Error parsing API response as JSON: {e}", file=sys.stderr)
        raise

def parse_and_flatten_data(data: dict) -> tuple:
    """Parses JSON data and returns a flattened record:
    (timestamp, temperature, windspeed, winddirection, weathercode, humidity)
    """
    try:
        current_weather = data.get("current_weather")
        if not current_weather:
            raise ValueError("API response is missing 'current_weather' section.")

        timestamp = current_weather.get("time")
        temperature = current_weather.get("temperature")
        windspeed = current_weather.get("windspeed")
        winddirection = current_weather.get("winddirection")
        weathercode = current_weather.get("weathercode")

        if timestamp is None:
            raise ValueError("Current weather data is missing 'time' field.")

        # Match humidity from hourly forecasts for the current weather timestamp
        hourly = data.get("hourly", {})
        hourly_times = hourly.get("time", [])
        hourly_humidity = hourly.get("relativehumidity_2m", [])

        humidity = None
        # Try direct match first
        if timestamp in hourly_times:
            idx = hourly_times.index(timestamp)
            if idx < len(hourly_humidity):
                humidity = hourly_humidity[idx]
        
        # Try matching by truncating minutes/seconds to start of the hour
        if humidity is None:
            try:
                if "T" in timestamp:
                    date_part, time_part = timestamp.split("T")
                    hour_part = time_part.split(":")[0]
                    truncated_timestamp = f"{date_part}T{hour_part}:00"
                    if truncated_timestamp in hourly_times:
                        idx = hourly_times.index(truncated_timestamp)
                        if idx < len(hourly_humidity):
                            humidity = hourly_humidity[idx]
            except Exception:
                pass
        
        if humidity is None:
            print(f"Warning: Could not find matching relative humidity for timestamp {timestamp}.", file=sys.stderr)

        return (timestamp, temperature, windspeed, winddirection, weathercode, humidity)
    except Exception as e:
        print(f"Error flattening API data: {e}", file=sys.stderr)
        raise

def store_in_database(db_name: str, record: tuple) -> None:
    """Stores the parsed weather record in the SQLite database."""
    print("Storing record in SQLite database...")
    try:
        with closing(sqlite3.connect(db_name)) as conn:
            with conn:  # Transaction auto-commit/rollback
                with closing(conn.cursor()) as cursor:
                    # Create table if it doesn't exist
                    cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                            timestamp TEXT PRIMARY KEY,
                            temperature REAL,
                            windspeed REAL,
                            winddirection REAL,
                            weathercode INTEGER,
                            humidity REAL
                        )
                    """)
                    
                    # Insert or replace record (if timestamp already exists, replace it to update values)
                    cursor.execute(f"""
                        INSERT OR REPLACE INTO {TABLE_NAME}
                        (timestamp, temperature, windspeed, winddirection, weathercode, humidity)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, record)
    except sqlite3.Error as e:
        print(f"SQLite database error occurred: {e}", file=sys.stderr)
        raise

def display_stored_data(db_name: str) -> None:
    """Retrieves all stored records and prints them as a formatted table."""
    try:
        with closing(sqlite3.connect(db_name)) as conn:
            with closing(conn.cursor()) as cursor:
                # Check if the table exists first
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{TABLE_NAME}'")
                if not cursor.fetchone():
                    print("No stored weather records found (table does not exist).")
                    return

                cursor.execute(f"""
                    SELECT timestamp, temperature, windspeed, winddirection, weathercode, humidity 
                    FROM {TABLE_NAME} 
                    ORDER BY timestamp ASC
                """)
                rows = cursor.fetchall()
                
                if not rows:
                    print("No records stored in database.")
                    return

                headers = [
                    "Timestamp", 
                    "Temperature (°C)", 
                    "Wind Speed (km/h)", 
                    "Wind Direction (°)", 
                    "Weather Code", 
                    "Humidity (%)"
                ]
                
                # Format wind direction and humidity to handle possible None values cleanly
                formatted_rows = []
                for row in rows:
                    formatted_rows.append([
                        row[0],
                        f"{row[1]:.1f}" if row[1] is not None else "N/A",
                        f"{row[2]:.1f}" if row[2] is not None else "N/A",
                        f"{int(row[3])}°" if row[3] is not None else "N/A",
                        row[4] if row[4] is not None else "N/A",
                        f"{int(row[5])}%" if row[5] is not None else "N/A"
                    ])

                print("\n=== Mumbai Weather Data History ===")
                print(tabulate(formatted_rows, headers=headers, tablefmt="grid"))
                print(f"Total records stored: {len(rows)}\n")
    except sqlite3.Error as e:
        print(f"SQLite database error occurred while fetching records: {e}", file=sys.stderr)
        raise

def main():
    try:
        # 1. Fetch weather data
        raw_data = fetch_weather_data(API_URL)
        
        # 2. Parse and flatten response
        record = parse_and_flatten_data(raw_data)
        print(f"Fetched and parsed current weather record for: {record[0]}")
        
        # 3. Store record in SQLite database
        store_in_database(DB_NAME, record)
        
        # 4. Print table of all stored data
        display_stored_data(DB_NAME)
        
    except Exception as e:
        print("Pipeline execution failed.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
