#!/usr/bin/env python3
"""
City Data Reporter
- Prompts for a city (with validation)
- Fetches live weather from OpenWeatherMap
- Prints a formatted summary
- Writes data to city_data.csv (with headers)
- Reads back the CSV and reports count + city/temperature list
"""

import os
import sys
import csv
import json
from pathlib import Path
from typing import Dict, Any, Optional

import requests  # pip install requests

CSV_FILE = Path("city_data.csv")
CSV_HEADERS = ["City", "Country", "Temperature (C)", "Humidity (%)", "Description"]
API_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_api_key() -> str:
    """
    Reads the API key from the OPENWEATHER_API_KEY environment variable,
    otherwise prompts the user once.
    """
    key = os.getenv("OPENWEATHER_API_KEY")
    if key and key.strip():
        return key.strip()

    print("No OPENWEATHER_API_KEY found in environment.")
    key = input("Enter your OpenWeatherMap API key: ").strip()
    if not key:
        print("An API key is required. Exiting.")
        sys.exit(1)
    return key


def prompt_city() -> str:
    """Prompt until the user provides a non-empty city name; normalize spacing/title-case."""
    while True:
        raw = input("Enter a city name: ").strip()
        if raw:
            # collapse internal whitespace and title-case for neatness
            normalized = " ".join(raw.split()).title()
            return normalized
        print("City name cannot be empty. Please try again.")


def fetch_weather(city: str, api_key: str) -> Dict[str, Any]:
    """
    Calls OpenWeatherMap for the given city. Returns the parsed JSON dict on success.
    Raises ValueError with a friendly message on known errors.
    """
    try:
        resp = requests.get(
            API_URL,
            params = {"q": city, "appid": api_key, "units": "metric"},
            timeout = 10,
        )
    except requests.RequestException as exc:
        raise ValueError(f"Network error contacting the API: {exc}") from exc

    # Try to decode JSON even on error for useful messages
    try:
        data = resp.json()
    except json.JSONDecodeError:
        data = {}

    if resp.status_code == 200:
        return data

    # Common error handling
    if resp.status_code == 401:
        raise ValueError("Unauthorized (401): Invalid or missing API key.")
    if resp.status_code == 404:
        # OWM uses code/message in body too
        msg = data.get("message", "City not found.")
        raise ValueError(f"Not found (404): {msg}")
    # Generic fallback
    raise ValueError(
        f"API error ({resp.status_code}): {data.get('message', 'Unexpected error')}"
    )


def parse_weather(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract required fields from the OWM response.
    Expected keys:
      - name (city)
      - sys.country
      - main.temp (C)
      - main.humidity
      - weather[0].description
    """
    city = data.get("name", "Unknown")
    country = (data.get("sys") or {}).get("country", "—")
    main = data.get("main") or {}
    temp_c = main.get("temp")
    humidity = main.get("humidity")
    weather_list = data.get("weather") or []
    description = (weather_list[0].get("description") if weather_list else "") or "n/a"

    # Basic sanity checks
    if temp_c is None or humidity is None:
        raise ValueError("API response missing temperature or humidity fields.")

    return {
        "City": city,
        "Country": country,
        "Temperature (C)": round(float(temp_c), 1),
        "Humidity (%)": int(humidity),
        "Description": description,
    }


def print_summary(row: Dict[str, Any]) -> None:
    """Pretty console output for a single row of city data."""
    print(
        f"\nWeather for {row['City']}, {row['Country']}: "
        f"{row['Description']} | "
        f"Temp: {row['Temperature (C)']}°C | "
        f"Humidity: {row['Humidity (%)']}%\n"
    )


def write_row_to_csv(row: Dict[str, Any], csv_path: Path = CSV_FILE) -> None:
    """Append a row to city_data.csv, writing headers if the file is new/empty."""
    file_exists = csv_path.exists()
    write_header = True
    if file_exists:
        try:
            write_header = csv_path.stat().st_size == 0
        except OSError:
            write_header = True

    with csv_path.open(mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def read_and_report(csv_path: Path = CSV_FILE) -> None:
    """
    Reads city_data.csv and reports the number of cities and a list of
    their names + temperatures.
    """
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        print("No CSV data to report yet.")
        return

    with csv_path.open(mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("No CSV data to report yet.")
        return

    print(f"Entries in {csv_path.name}: {len(rows)}")
    for r in rows:
        city = r.get("City", "Unknown")
        temp = r.get("Temperature (C)", "n/a")
        print(f" - {city}: {temp}°C")


def main() -> None:
    api_key = get_api_key()
    city = prompt_city()

    try:
        raw_data = fetch_weather(city, api_key)
        parsed = parse_weather(raw_data)
    except ValueError as err:
        print(f"Error: {err}")
        sys.exit(1)

    print_summary(parsed)
    write_row_to_csv(parsed)
    read_and_report()


if __name__ == "__main__":
    main()
