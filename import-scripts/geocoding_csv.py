# coding=utf-8

import csv
import os
import geopandas as gpd
from shapely.geometry import Point
from geopy.geocoders import Nominatim, GoogleV3
from dotenv import load_dotenv
import time


INTERVAL_CALL_IN_SECONDS = 0.5

# Load environment variables from .env file
load_dotenv()


def get_address(row, retry=1):
    """Returns a list of address components based on row data."""
    address = []
    if retry == 1:
        if row[0] and row[0] != 'Cnr':
            address.append(row[0].strip())
        if row[1]:
            address.append(row[1].strip())
        if row[2]:
            address.append(row[2].strip())
        if row[3]:
            address.append(row[3].strip())
        if row[4]:
            address.append(row[4].strip())
    if retry == 2:
        if row[0] and row[0] != 'Cnr':
            address.append(row[0].strip())
        if row[1]:
            address.append(row[1].strip())
        if row[2] and row[2] != row[1]:
            address.append(row[2].strip())
        if row[3] and row[3] != row[2]:
            address.append(row[3].strip())
        if row[4]:
            address.append(row[4].strip())
    return address


def call_geocode(geolocator, address):
    if isinstance(geolocator, Nominatim):
        return geolocator.geocode(address)
    elif isinstance(geolocator, GoogleV3):
        return geolocator.geocode(address, region='ZA')


def do_geocode(geolocator, address_1, address_2):
    # First attempt to geocode
    location = call_geocode(geolocator, address_1)
    if location:
        return location, address_1
    elif address_1 != address_2:
        time.sleep(INTERVAL_CALL_IN_SECONDS)
        # Second attempt with a different address format
        if address_2:
            location = call_geocode(geolocator, address_2)
            if location:
                return location, address_2

    return None, None

def process(input_csv, output_shapefile):
    """Geocode the addresses in the input CSV file and save the results in a shapefile."""
    
    # Initialize the Nominatim geolocator correctly
    geolocator_dict  = {
        'Nominatim': Nominatim(timeout=20, country_bias='ZA'),
        'GoogleV3': GoogleV3(
            api_key=os.getenv('GOOGLE_API_KEY'), timeout=20,
            filter_less_accurate=True
        )
    }

    points = []
    addresses = []
    sources = []
    
    if not os.path.exists(input_csv):
        print(f"Error: Input file {input_csv} does not exist.")
        return
    
    with open(input_csv, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row

        for idx, row in enumerate(reader):
            address = get_address(row, 1)
            address_1 = ', '.join(address)
            address = get_address(row, 2)
            address_2 = ', '.join(address)

            if address_1:
                for source_key, geolocator in geolocator_dict.items():
                    location, address_str = do_geocode(geolocator, address_1, address_2)
                    if location:
                        points.append(Point(location.longitude, location.latitude))
                        addresses.append(address_str)
                        sources.append(source_key)
                        break
                    else:
                        # try next geolocator
                        time.sleep(INTERVAL_CALL_IN_SECONDS)
            
            # Add a small delay to avoid overloading Nominatim's servers
            time.sleep(INTERVAL_CALL_IN_SECONDS)

    # Create a GeoDataFrame and save to shapefile
    gdf = gpd.GeoDataFrame({'Address': addresses, 'Source': sources}, geometry=points, crs="EPSG:4326")
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
