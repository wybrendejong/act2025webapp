import pandas as pd
import geopandas as gpd
import folium
from folium import Choropleth

def empty_map() -> folium.Map:
    """Returns a folium map centered on the Netherlands without any data"""
    center = (52, 5)
    m = folium.Map(location=center, zoom_start=6, tiles='cartodbpositron')

    return m


def update_map(gdf: gpd.GeoDataFrame) -> folium.Map:
    """Takes a GeoDataFrame with a prob_positive column and postcode areas and plots the data in a folium map"""
    gdf = gdf.reset_index()
    gdf = gdf.to_crs(epsg=4326)

    last_month = gdf['month'].max()

    gdf = gdf[gdf['month'] == last_month]
    gdf['month'] = gdf['month'].astype(str)

    # Create folium map centered on the mean coordinates
    center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
    m = folium.Map(location=center, zoom_start=8, tiles='cartodbpositron', width='100%', height='100%')

    # Add polygons colored by predicted probability
    Choropleth(
        geo_data=gdf,
        data=gdf,
        columns=['postcode','prob_positive'],
        key_on='feature.properties.postcode',
        bins=[x/10 for x in range(11)],
        fill_color='Blues',
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name='Probability of Rat Sighting'
    ).add_to(m)

    # Add tooltips
    for i, row in gdf.iterrows():
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x, p=row: {
                'fillColor': '#00000000',
                'color': '#00000000',
                'weight': 0
            },
            tooltip=folium.Tooltip(
                f"Postcode: {row['postcode']}<br>"
                f"Likelihood of rats present: {row['prob_positive']:.1%}<br>"
            )
        ).add_to(m)

    return m