# Imports
import pandas as pd
import geopandas as gpd
import numpy as np

def load_bin_data(path):
    "Loads bin data from the file at _path_ and returns a dataframe with bins_per_km2 for each PC4 area"
    bin_df = pd.read_csv(path)
    bin_df = bin_df.rename({'PC4': 'postcode'}, axis=1)
    bin_df = bin_df.set_index('postcode')

    return bin_df['bins_per_km'].rename('bins_per_km2')

def load_manhole_data(path):
    "Loads manhole cover data from the file at _path_ and returns a dataframe with manholes_per_km2 for each PC4 area"
    manhole_df = pd.read_csv(path)
    manhole_df = manhole_df.rename({'PC4': 'postcode'}, axis=1)
    manhole_df = manhole_df.set_index('postcode')

    return manhole_df['put_per_km'].rename('manholes_per_km2')

def load_green_data(path):
    "Loads greenery data from the file at _path_ and returns a dataframe with green_percentage for each PC4 area"
    green_df = pd.read_csv(path)
    green_df = green_df.rename({'PC4': 'postcode', 'MEAN': 'green_percentage'}, axis=1)
    green_df = green_df.set_index('postcode')

    return green_df['green_percentage']

def load_water_data(path):
    "Loads water availability data from the file at _path_ and returns a dataframe with water_availability for each PC4 area"
    water_df = pd.read_csv(path)
    water_df = water_df.rename({'PC4': 'postcode', 'MEAN': 'green_percentage'}, axis=1)
    water_df = water_df.set_index('postcode')

    return water_df['Coverage_pct'].rename('water_availability')