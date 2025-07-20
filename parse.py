#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wanderlog to KML Converter
==========================

Convert Wanderlog travel itineraries to KML format for Google Earth/Maps.

Author: Sidorenko Danil <[danilden1@yandex.ru]>
GitHub: https://github.com/danilden1/Wanderlog-to-KML
License: MIT
Version: 1.0.0
Created: 2023-08-20

Features:
- Extract locations with metadata from Wanderlog trips
- Generate single or date-split KML files
- Preserve original trip structure and names
"""

import json
import re
import argparse
from xml.etree import ElementTree as ET
from xml.dom import minidom
from collections import defaultdict

def parse_arguments():
    parser = argparse.ArgumentParser(description='Convert trip data from HTML to KML')
    parser.add_argument('input_file', help='Path to input HTML file')
    parser.add_argument('--split', action='store_true', help='Split into separate KML files by date')
    parser.add_argument('--output', help='Base name for output files (default: trip title)')
    return parser.parse_args()

def extract_data(html_content):
    # Extract title
    title_match = re.search(r'<title.*?>(.*?) – Wanderlog</title>', html_content)
    title = title_match.group(1).strip() if title_match else "My Trip"
    
    # Extract JSON data
    json_match = re.search(r'window\.__MOBX_STATE__\s*=\s*({.*?});', html_content, re.DOTALL)
    if not json_match:
        raise ValueError("No JSON data found in HTML")

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
                    
                    places.append({
                        'name': place['name'],
                        'lat': place['geometry']['location']['lat'],
                        'lng': place['geometry']['location']['lng'],
                        'date': date,
                        'day_month': day_month
                    })
                except KeyError:
                    continue
    
    return title, places

def create_kml(places, filename, title, show_dates=False):
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
    with open(filename, 'wb') as f:
        f.write(xml_str)

def main():
    args = parse_arguments()
    
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            html = f.read()
    except IOError as e:
        print(f"Error reading file: {e}")
        return

    try:
        title, places = extract_data(html)
    except ValueError as e:
        print(f"Error processing data: {e}")
        return

    if not places:
        print("No places found in the trip data")
        return

    # Clean title for filename
    base_name = re.sub(r'[^\w-]', '_', args.output or title).lower()
    
    # Create combined KML
    create_kml(
        places, 
        f"{base_name}_combined.kml", 
        title, 
        show_dates=True
    )
    print(f"Created: {base_name}_combined.kml")

    # Create split KMLs if requested
    if args.split:
        by_date = defaultdict(list)
        for place in places:
            date_key = place['date'] or 'no_date'
            by_date[date_key].append(place)
        
        for date, places in by_date.items():
            date_str = date.replace('-', '_') if date != 'no_date' else date
            create_kml(
                places,
                f"{base_name}_{date_str}.kml",
                f"{title} - {date}" if date != 'no_date' else f"{title} - No Date",
                show_dates=False
            )
            print(f"Created: {base_name}_{date_str}.kml")

if __name__ == "__main__":
    main()