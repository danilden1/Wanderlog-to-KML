# Wanderlog Trip to KML Converter

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)

Convert your Wanderlog travel itineraries to KML format for use in [Google Maps](https://www.google.com/maps), [Maps.me](https://maps.me/), [Organic Maps](https://organicmaps.app/ru/) and other GIS applications.

![alt text](https://github.com/danilden1/Wanderlog-to-KML/blob/main/doc/klm_usage.JPG?raw=true)


## Features

- Extract all locations from Wanderlog trips
- Preserve location names and coordinates
- Option to split by travel dates
- Clean KML output compatible with most mapping tools
- Preserve original trip title and organization

## Prerequisites

- Python 3.8+
- Chrome or Firefox browser

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/danilden1/Wanderlog-to-KML
   cd wanderlog-to-kml 
   ```
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
## How to Export Your Wanderlog Trip
1. Open your trip in Wanderlog (https://wanderlog.com)
2. Open Developer Tools:

    Windows/Linux: Ctrl+Shift+I

    Mac: Command+Option+I

3. Go to the Source tab
4. Find your trip in **wanderlog.com** folder
5. Save file

![alt text](https://github.com/danilden1/Wanderlog-to-KML/blob/main/doc/klm.JPG?raw=true)


## Usage
### Basic Conversion
```bash
python3 wanderlog_to_kml.py my_trip.html
```
Creates my_trip_combined.kml with all locations.

### Advanced Options
|Option|Description|
|-|-|
|--split|Split into separate KML files by date|
|--output NAME|Custom base name for output files|
### Example:

```bash
python3 parse.py my_trip.html --split --output europe_trip
```
#### Output Files
[name]_combined.kml - All locations in one file

[name]_YYYY_MM_DD.kml - Locations by date (with --split)

[name]_no_date.kml - Locations without dates (with --split)

#### Example Output Structure

europe_trip_combined.kml

europe_trip_2023_06_15.kml

europe_trip_2023_06_16.kml

europe_trip_no_date.kml

## Contributing
Pull requests are welcome! For major changes, please open an issue first.

## License
MIT


## Tests
Tested 20.07.2025 