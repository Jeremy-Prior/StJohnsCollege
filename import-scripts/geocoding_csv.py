# coding=utf-8

import csv
import os
import geopandas as gpd
from shapely.geometry import Point
from geopy.geocoders import Nominatim
import time

def get_address(row, retry=1):
    """Returns a list of address components based on row data."""
    address = []
    if retry == 1:
        if row[1] and row[1] != 'Cnr':
            address.append(row[1].strip())
        if row[2]:
            address.append(row[2].strip())
        if row[3]:
            address.append(row[3].strip())
        if row[4]:
            address.append(row[4].strip())
        if row[5]:
            address.append(row[5].strip())
    if retry == 2:
        if row[1] and row[1] != 'Cnr':
            address.append(row[1].strip())
        if row[2]:
            address.append(row[2].strip())
        if row[3] and row[3] != row[2]:
            address.append(row[3].strip())
        if row[4] and row[4] != row[3]:
            address.append(row[4].strip())
        if row[5]:
            address.append(row[5].strip())
    return address

from geopy.geocoders import Nominatim
import time

def process(input_csv, output_shapefile):
    """Geocode the addresses in the input CSV file and save the results in a shapefile."""
    
    # Initialize the Nominatim geolocator correctly
    geolocator = Nominatim(timeout=20)
    
    points = []
    addresses = []
    
    if not os.path.exists(input_csv):
        print(f"Error: Input file {input_csv} does not exist.")
        return
    
    with open(input_csv, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        
        for row in reader:
            address = get_address(row, 1)
            address_str = ','.join(address)
            
            if address_str:
                # First attempt to geocode the address using Nominatim
                location = geolocator.geocode(address_str, country_codes='ZA')
                if location:
                    points.append(Point(location.longitude, location.latitude))
                    addresses.append(address_str)
                else:
                    # Second attempt with a different address format
                    address = get_address(row, 2)
                    address_str = ','.join(address)
                    if address_str:
                        location = geolocator.geocode(address_str, country_codes='ZA')
                        if location:
                            points.append(Point(location.longitude, location.latitude))
                            addresses.append(address_str)
            
            # Add a small delay to avoid overloading Nominatim's servers
            time.sleep(1)
    
    # Create a GeoDataFrame and save to shapefile
    gdf = gpd.GeoDataFrame({'Address': addresses}, geometry=points, crs="EPSG:4326")
    gdf.to_file(output_shapefile)
    print(f"Shapefile saved to {output_shapefile}")

def test():
    """Test geocoding."""
    geolocator = Nominatim()
    result = geolocator.geocode("KALKFONTEIN, KALKFONTEIN, KUILSRIVIER")
    print(result.raw)

# Uncomment below to test
# test()

# Example usage
input_csv_file = '../../../Geomapping_Parents_Address_20240731.csv'  # Path to the input CSV file
output_shapefile = '../../../geocoded_points.shp'  # Path for the output shapefile

process(input_csv_file, output_shapefile)
