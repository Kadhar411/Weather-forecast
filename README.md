# Weather Data Pipeline

A simple Python-based weather data pipeline that fetches weather data for Mumbai from the Open-Meteo API, flattens the JSON response, stores it in a SQLite database, and prints a history of stored records as a formatted table.

## Project Structure

- `weather_pipeline.py`: The main pipeline script that fetches, parses, stores, and displays the weather data.
- `requirements.txt`: Project dependencies (`requests` and `tabulate`).
- `weather.db`: SQLite database file (automatically created on the first run).
- `README.md`: Setup and usage instructions.

## Prerequisites

- Python 3.7 or higher installed on your system.

## Setup Instructions

1. Clone or copy this repository to your local machine.
2. Open a terminal (PowerShell, Command Prompt, or bash) and navigate to the project directory:
   ```bash
   cd "C:\Users\AbdulkadharSuhail\projects\Project sub"
   ```
3. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
4. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD)**:
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - **macOS/Linux**:
     ```bash
     source .venv/bin/activate
     ```
5. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage Instructions

To run the pipeline and fetch the latest weather data:

```bash
python weather_pipeline.py
```

### Script Behavior

On each run, the script will:
1. Fetch live weather data for Mumbai from the Open-Meteo API.
2. Extract the current weather metrics (`timestamp`, `temperature`, `windspeed`, `winddirection`, `weathercode`).
3. Match the current weather timestamp with the corresponding `humidity` from the hourly forecasting data returned in the same payload.
4. Establish a connection to the SQLite database (`weather.db`).
5. Create the `weather_data` table if it does not already exist.
6. Insert or replace the weather record based on the `timestamp` primary key (preventing duplicate rows if executed multiple times in the same hour).
7. Print a formatted historical table of all saved entries using the `tabulate` library.

## Database Schema (`weather.db`)

The database `weather.db` contains a table named `weather_data` with the following structure:

| Column | SQLite Type | Description |
|---|---|---|
| `timestamp` | TEXT | ISO8601 date and time string (Primary Key) |
| `temperature` | REAL | Temperature in degrees Celsius (°C) |
| `windspeed` | REAL | Wind speed in kilometers per hour (km/h) |
| `winddirection` | REAL | Wind direction in degrees (°) |
| `weathercode` | INTEGER | WMO weather code |
| `humidity` | REAL | Relative humidity percentage (%) |

## Error Handling

- **Network Failures**: Catches issues like DNS errors, timeouts, or API unavailability.
- **Data Parsing Errors**: Checks for missing fields in the JSON response, falling back safely if hourly humidity matches aren't found.
- **Database Errors**: Safe execution using transactions and closing DB resources properly in a `finally` block or utilizing context managers.
