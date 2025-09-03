#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wanderlog to KML Converter
==========================

Convert Wanderlog travel itineraries to KML format for Google Earth/Maps.

Author: Sidorenko Danil <[danilden1@yandex.ru]>
GitHub: https://github.com/danilden1/Wanderlog-to-KML
License: MIT
Version: 1.1.0
Created: 2023-08-20
Updated: 2025-08-15

Features:
- Extract locations with metadata from Wanderlog trips
- Generate single or date-split KML files
- Preserve original trip structure and names
- Specify custom output directory for generated files
- Progress and summary reporting
"""

import json
import re
import argparse
import os
from xml.etree import ElementTree as ET
from collections import defaultdict

def parse_arguments():
    """
    Parse command-line arguments for the converter.

    Returns:
        argparse.Namespace: Parsed arguments with input_file, split, output, outdir.
    """
    parser = argparse.ArgumentParser(description='Convert Wanderlog trip HTML to KML format')
    parser.add_argument('input_file', help='Path to input HTML file')
    parser.add_argument('--split', action='store_true', help='Split into separate KML files by date')
    parser.add_argument('--output', help='Base name for output files (default: trip title)')
    parser.add_argument('--outdir', default='.', help='Directory to save output files (default: current directory)')
    return parser.parse_args()

def extract_data(html_content):
    """
    Extract trip title and location data from Wanderlog HTML export.

    Args:
        html_content (str): HTML content of exported Wanderlog trip.

    Returns:
        tuple: (title, places) where title is the trip name and places is a list of dicts.

    Raises:
        ValueError: If parsing fails or required data is missing.
    """
    # Extract title
    title_match = re.search(r'<title.*?>(.*?) – Wanderlog</title>', html_content)
    title = title_match.group(1).strip() if title_match else "My Trip"
    
    # Extract JSON data
    json_match = re.search(r'window\.__MOBX_STATE__\s*=\s*({.*?});', html_content, re.DOTALL)
    if not json_match:
        raise ValueError("No JSON data found in HTML. Make sure you exported the correct Wanderlog page.")

    try:
        data = json.loads(json_match.group(1))
        trip_plan = data['tripPlanStore']['data']['tripPlan']
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Error parsing trip data: {str(e)}")

    # Build block_id to date mapping
    block_to_date = {}
    for expense in trip_plan['itinerary']['budget'].get('expenses', []):
        if 'blockId' in expense and 'associatedDate' in expense:
            block_to_date[expense['blockId']] = expense['associatedDate']

    # Extract places
    places = []
    for section in trip_plan['itinerary']['sections']:
        if 'blocks' not in section:
            continue
        for block in section['blocks']:
            if block.get('type') == 'place' and 'place' in block:
                place = block['place']
                try:
                    date = block_to_date.get(block['id'], section.get('date', ''))
                    day_month = f"{date[8:10]}.{date[5:7]}" if date else ""
                    lat = place['geometry']['location']['lat']
                    lng = place['geometry']['location']['lng']
                    if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
                        continue  # Skip invalid coordinates
                    places.append({
                        'name': place['name'],
                        'lat': lat,
                        'lng': lng,
                        'date': date,
                        'day_month': day_month
                    })
                except (KeyError, TypeError):
                    continue
    
    return title, places

def create_kml(places, filename, title, show_dates=False):
    """
    Generate a KML file from a list of place dictionaries.

    Args:
        places (list): List of dicts with keys 'name', 'lat', 'lng', 'date', 'day_month'.
        filename (str): Output path for the KML file.
        title (str): KML document name.
        show_dates (bool): If True, include the day/month in the placemark name.
    """
    kml = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
    doc = ET.SubElement(kml, 'Document')
    ET.SubElement(doc, 'name').text = title
    
    for place in places:
        pm = ET.SubElement(doc, 'Placemark')
        name = ET.SubElement(pm, 'name')
        name.text = f"[{place['day_month']}] {place['name']}" if show_dates and place['day_month'] else place['name']
        
        pt = ET.SubElement(pm, 'Point')
        ET.SubElement(pt, 'coordinates').text = f"{place['lng']},{place['lat']},0"
        
        if place['date']:
            ext = ET.SubElement(pm, 'ExtendedData')
            data = ET.SubElement(ext, 'Data', name='date')
            ET.SubElement(data, 'value').text = place['date']
    
    # Write to file
    xml_str = ET.tostring(kml, encoding='utf-8', xml_declaration=True)
    try:
        with open(filename, 'wb') as f:
            f.write(xml_str)
    except IOError as e:
        print(f"Error writing KML file {filename}: {e}")

def main():
    """
    Main function for CLI usage.
    """
    args = parse_arguments()
    outdir = os.path.abspath(args.outdir)
    if not os.path.exists(outdir):
        try:
            os.makedirs(outdir)
            print(f"Created output directory: {outdir}")
        except Exception as e:
            print(f"Failed to create output directory '{outdir}': {e}")
            return

    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            html = f.read()
    except IOError as e:
        print(f"Error reading input file: {e}")
        return

    try:
        title, places = extract_data(html)
    except ValueError as e:
        print(f"Error processing data: {e}")
        return

    if not places:
        print("No places found in the trip data. Check that your Wanderlog export is correct.")
        return

    base_name = re.sub(r'[^\w-]', '_', args.output or title).lower()
    
    # Create combined KML
    combined_path = os.path.join(outdir, f"{base_name}_combined.kml")
    create_kml(places, combined_path, title, show_dates=True)
    print(f"Created: {combined_path}")

    generated_files = [combined_path]

    # Create split KMLs if requested
    if args.split:
        by_date = defaultdict(list)
        for place in places:
            date_key = place['date'] or 'no_date'
            by_date[date_key].append(place)
        for date, places_for_date in by_date.items():
            date_str = date.replace('-', '_') if date != 'no_date' else date
            split_path = os.path.join(outdir, f"{base_name}_{date_str}.kml")
            split_title = f"{title} - {date}" if date != 'no_date' else f"{title} - No Date"
            create_kml(places_for_date, split_path, split_title, show_dates=False)
            print(f"Created: {split_path}")
            generated_files.append(split_path)

    # Print summary
    print("\nSummary:")
    print(f"Trip title: {title}")
    print(f"Total places processed: {len(places)}")
    print(f"Files generated: {len(generated_files)}")
    for fpath in generated_files:
        print(f" - {fpath}")

if __name__ == "__main__":
    main()
