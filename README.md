# Weather Reporter

A simple Python command-line application that retrieves live weather data for a city using the OpenWeatherMap API, displays it to the user, and stores it in a CSV file.

# Features
- Interactive city name input with validation (no empty input allowed).
- Live weather data from OpenWeatherMap (temperature, humidity, description).
- Graceful error handling for missing cities or bad API keys.
- Writes data to `city_data.csv` with headers.
- Reads the CSV back and reports number of cities + temperatures.
