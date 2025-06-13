# Imports
import pandas as pd
import geopandas as gpd
import numpy as np

bouwjaar_means = [
    ('aantal_woningen_bouwjaar_voor_1945', 1930),
    ('aantal_woningen_bouwjaar_45_tot_65', 1955),
    ('aantal_woningen_bouwjaar_65_tot_75', 1970),
    ('aantal_woningen_bouwjaar_75_tot_85', 1980),
    ('aantal_woningen_bouwjaar_85_tot_95', 1990),
    ('aantal_woningen_bouwjaar_95_tot_05', 2000),
    ('aantal_woningen_bouwjaar_05_tot_15', 2010),
    ('aantal_woningen_bouwjaar_na_2015', 2018)
]


def load_cbs_data(path, drop_empty_cols=False):
    """Loads a cbs regional statistics geopackage into a geopandas geodataframe. 
   
    Takes a file path and keyword arguments, loads data into a geodataframe and pre-processes the data.
    Returns a geodataframe, optionally with empty columns removed.

    Args:
        path (str): The file path to load. The file should be a geopackage of cbs regional statistics by PC4 area.
        drop_empty_cols (bool, False): When True, drop columns that don't contain any data.
    """
    cbs_df = gpd.read_file(path)

    # reset CBS index to postal code
    cbs_df.set_index('postcode', inplace=True)
    cbs_df.sort_index(inplace=True)

    # set nan values
    cbs_df.replace(-99995, np.nan, inplace=True)
    cbs_df.replace(-99997, np.nan, inplace=True)
    cbs_df.replace(-99995.0, np.nan, inplace=True)
    cbs_df.replace(-99997.0, np.nan, inplace=True)

    # Reproject to a projected CRS (Amersfoort / RD New)
    cbs_df = cbs_df.to_crs(epsg=28992)

    # Calculate area in km2
    cbs_df['area_km2'] = cbs_df.geometry.area / 1e6

    # Calculate population density (inwoners per km2)
    cbs_df['inwoner_dichtheid'] = cbs_df['aantal_inwoners'] / cbs_df['area_km2']

    # calculate average bouwjaar in the data
    cbs_df['bouwjaar_gemiddeld'] = cbs_df.apply(calc_bouwjaar_gemiddeld, axis=1)

    if drop_empty_cols:
        cbs_df = cbs_df.dropna(axis=1, how='all')

    return cbs_df


def calc_bouwjaar_gemiddeld(row):
    """Calculates the averege building year 'bouwjaar_gemiddeld' for a row in the cbs data."""
    total = 0
    count = 0
    for col, year in bouwjaar_means:
        n = row.get(col, np.nan)
        if pd.notnull(n):
            total += n * year
            count += n

    return total / count if count > 0 else np.nan


def aantal_to_percentage(df):
    """Converts all 'aantal' columns (except 'aantal_inwoners' and 'aantal_woningen') to percentage columns."""
    for col in df.columns:
        if col.startswith('aantal_') and col not in ['aantal_inwoners', 'aantal_woningen']:
            if 'woningen' in col:
                denom = df['aantal_woningen']
            else:
                denom = df['aantal_inwoners']

            perc_col = col.replace('aantal_', 'percentage_')

            df[perc_col] = df[col] / denom * 100
            df.drop(columns=col, inplace=True)

    return df


def drop_empty_cols(df, max_na_percentage=0.0):
    """Drops columns with more no data values than max_na_percentage (float)"""
    min_non_na = int((1 - max_na_percentage) * len(df))
    cleaned_df = df.dropna(axis=1, thresh=min_non_na)

    return cleaned_df

