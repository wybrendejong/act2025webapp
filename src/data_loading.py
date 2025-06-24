# Imports
import pandas as pd
import geopandas as gpd
import numpy as np
import libpysal
from libpysal.weights import Queen


def load_rm_data(io) -> pd.DataFrame:
    """
    Loads rat monitor export data into a pandas dataframe. 
   
    Takes a file path and keyword arguments, loads data into a dataframa and pre-processes the data.
    Returns a dataframe with all data (for the selected year) from the rat monitor export file.

    Args:
        io: A file path or IO object that refers to the rat monitor data file.

    Returns:
        DataFrame: A pre-processed DataFrame with the rat monitor data.
    """
    # load rat monitor data into dataframe
    rat_df = pd.read_excel(io)

    # clean weird characters
    rat_df.columns = rat_df.columns.str.strip('\n')
    rat_df = rat_df.map(lambda x: x.strip('[').strip(']') if isinstance(x, str) else x)

    # set nan values
    rat_df.replace('[]', np.nan, inplace=True)

    # correct datatypes
    rat_df['Pc4code'] = rat_df['Pc4code'].fillna(0000).astype(float).astype(int)
    rat_df['Datum waarneming'] = pd.to_datetime(rat_df['Datum waarneming'])
    rat_df['Einddatum'] = pd.to_datetime(rat_df['Einddatum'])

    return rat_df


def transform_to_spatiotemporal_gdf(rat_df, pc_gdf, rolling_stat_window=6) -> gpd.GeoDataFrame:
    """
    Transforms rat sighting data and postcode geometries into a spatiotemporal GeoDataFrame with temporal and spatial features.
    
    This function aggregates rat sighting counts by month and postcode, fills missing combinations with zeros,
    and computes temporal features such as lags and rolling statistics. It also computes spatial lag features
    using Queen contiguity weights based on the provided postcode geometries.
    
    Args:
        rat_df (DataFrame): DataFrame containing rat sighting records. Must include columns 'Datum waarneming' (datetime) and 'Pc4code' (postcode).
        pc_gdf (GeoDataFrame): GeoDataFrame containing postcode geometries. The index should correspond to postcode values.
        rolling_stat_window (int default 6): Window size for rolling statistics (mean, max, std) on rat sighting counts, by postcode. Default is 6.
    
    Returns:
        GeoDataFrame: A GeoDataFrame indexed by month and postcode, containing:
            - 'TOTAAL': monthly rat sighting counts
            - 'TOTAAL_lag1', 'TOTAAL_lag2': temporal lags of counts
            - 'rolling_mean', 'rolling_max', 'rolling_std': rolling statistics of counts
            - 'spatial_lag': spatial lag of counts for each month
            - 'spatial_lag_prev': spatial lag from the previous month (to prevent data leakage)
            - 'geometry': geometry of the postcode
    """
    rat_df['month'] = rat_df['Datum waarneming'].dt.to_period('M').dt.to_timestamp()

    # Create index for all months and all postcodes
    all_months = pd.date_range(rat_df['month'].min(), rat_df['month'].max(), freq='MS')
    all_postcodes = pc_gdf.index.unique()
    idx = pd.MultiIndex.from_product([all_months, all_postcodes], names=['month', 'postcode'])

    # Group rat sightinhs by month and postcode
    monthly_df = (
        rat_df.groupby(['month', 'Pc4code'])
        .size()
        .reset_index(name='TOTAAL')
        .rename(columns={'Pc4code': 'postcode'})
    )

    # Reindex to include all months and postcods, filling with 0 for all non rat sightings
    monthly_df = monthly_df.set_index(['month', 'postcode']).reindex(idx, fill_value=0).reset_index()

    # Sort for lag calculation
    monthly_df = monthly_df.sort_values(['postcode', 'month'])

    # Add temporal lags (e.g., previous month and two months ago)
    monthly_df['TOTAAL_lag1'] = monthly_df.groupby('postcode')['TOTAAL'].shift(1)
    monthly_df['TOTAAL_lag2'] = monthly_df.groupby('postcode')['TOTAAL'].shift(2)

    # Add rolling statistics for
    monthly_df['rolling_mean'] = (
        monthly_df.groupby('postcode')['TOTAAL']
        .transform(lambda x: x.shift(1).rolling(window=rolling_stat_window, min_periods=1).mean())
    )
    monthly_df['rolling_max'] = (
        monthly_df.groupby('postcode')['TOTAAL']
        .transform(lambda x: x.shift(1).rolling(window=rolling_stat_window, min_periods=1).max())
    )
    monthly_df['rolling_std'] = (
        monthly_df.groupby('postcode')['TOTAAL']
        .transform(lambda x: x.shift(1).rolling(window=rolling_stat_window, min_periods=1).std())
    )

    # Merge with geometry
    spatiotemporal_gdf = monthly_df.merge(pc_gdf[['geometry']], left_on='postcode', right_index=True)
    spatiotemporal_gdf = gpd.GeoDataFrame(spatiotemporal_gdf, geometry='geometry')

    # Create spatial weights (once)
    w = Queen.from_dataframe(pc_gdf)

    # Compute spatial lag for each month
    spatiotemporal_gdf['spatial_lag'] = 0.0
    for date in spatiotemporal_gdf['month'].unique():
        mask = spatiotemporal_gdf['month'] == date
        df_month = spatiotemporal_gdf[mask].set_index('postcode').reindex(pc_gdf.index)
        df_month.loc[:, df_month.columns != 'geometry'] = df_month.loc[:, df_month.columns != 'geometry'].fillna(0)
        lag = libpysal.weights.lag_spatial(w, df_month['TOTAAL'])
        spatiotemporal_gdf.loc[mask, 'spatial_lag'] = lag

    # Create a column with the spatial lag of the previous month to prevent data leakage
    spatiotemporal_gdf = spatiotemporal_gdf.sort_values(['postcode', 'month'])
    spatiotemporal_gdf['spatial_lag_prev'] = spatiotemporal_gdf.groupby('postcode')['spatial_lag'].shift(1)

    return spatiotemporal_gdf


def load_pc_geodata(path) -> gpd.GeoDataFrame:
    """
    Loads a geopackage with postal codes into a geopandas geodataframe. 
   
    Takes a file path, loads data into a geodataframe and pre-processes the data.
    Returns a cleaned geodataframe with geometry and postcode.
    """
    pc_gdf = gpd.read_file(path)

    # reset CBS index to postal code
    pc_gdf = pc_gdf.sort_values(by='postcode')[['postcode', 'geometry']]

    # set nan values
    pc_gdf.replace(-99995, np.nan, inplace=True)
    pc_gdf.replace(-99997, np.nan, inplace=True)
    pc_gdf.replace(-99995.0, np.nan, inplace=True)
    pc_gdf.replace(-99997.0, np.nan, inplace=True)

    # Reproject to a projected CRS (Amersfoort / RD New)
    pc_gdf = pc_gdf.to_crs(epsg=28992)

    return pc_gdf
