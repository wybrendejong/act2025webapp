""""
# ACT
# webGUI
"""
from nicegui import ui, html, app
from fastapi.staticfiles import StaticFiles
import json
import geopandas as gpd
import folium
import pandas as pd
import branca.colormap as cm
from pathlib import Path
import os

class Demo:
    def __init__(self):
        self.number = 1


def scriptInit():

    if not os.path.exists('map'):
        os.makedirs('map')
    if not os.path.exists('data'):
        os.makedirs('data')
    
    app.mount("/map", StaticFiles(directory="map"), name="map")

    

def mapSetup(gpkg_path, map_width, map_height):
    # Load your GeoDataFrame
    rat_gdf = gpd.read_file(gpkg_path, layer="my_layer")
    rat_gdf = rat_gdf.set_geometry("geometry")
    rat_gdf = rat_gdf[rat_gdf.geometry.notnull()]
    rat_gdf["TOTAAL"] = pd.to_numeric(rat_gdf["TOTAAL"], errors="coerce")
    rat_gdf = rat_gdf[rat_gdf["TOTAAL"].notnull()]

    # project data to correct coordinate system
    rat_gdf = rat_gdf.to_crs(epsg=4326)


    # Create a colormap based on the TOTAAL column
    min_val = rat_gdf["TOTAAL"].min()
    max_val = rat_gdf["TOTAAL"].max()
    colormap = cm.linear.YlOrRd_09.scale(min_val, max_val)
    colormap.caption = "TOTAAL"

    # zoom into amsterdam/netherlands
    center = [52.375, 4.935]
    m = folium.Map(
        location=center,
        zoom_start=9,
        control_scale=True,
        width=map_width,
        height=map_height,
    )
    m.get_root().width = f"{map_width}px"
    m.get_root().height = f"{map_height}px"

    # Add each polygon with a fill color from the colormap
    for _, row in rat_gdf.iterrows():
        geom = row["geometry"].simplify(0.001)
        value = row["TOTAAL"]
        color = colormap(value)

        feature = {
            "type": "Feature",
            "geometry": json.loads(gpd.GeoSeries([geom]).to_json())["features"][0]["geometry"],
            "properties": {"TOTAAL": value}
        }

        folium.GeoJson(
            data=feature,
            style_function=lambda feature, color=color: {
                "fillColor": color,
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.7
            },
            tooltip=folium.Tooltip(f"TOTAAL: {value}")
        ).add_to(m)

    colormap.add_to(m)
    iframe = m.get_root()._repr_html_()
    m.save("./map/map.html")
    return(iframe)






# def UISetup():
#     with ui.grid().classes('grid; grid-cols-1 md:grid-cols-[3fr_1fr] w-full gap-5'):
#         with ui.card():
#             ui.html("<b>Rat Monitor</b>").style('font-size: 24pt')
#         with ui.card():
#             dark = ui.dark_mode()
#             ui.switch('Dark mode').bind_value(dark)

#     with ui.grid().classes('grid grid-cols-1 md:grid-cols-[3fr_1fr] w-full gap-5'):
#         with ui.card().tight():
#             m = ui.leaflet(center=(52.375, 4.935)).style('width: 100%; position: relative; padding-top: 60%;')
#             m.tile_layer(
#                 url_template=r'https://tiles.stadiamaps.com/tiles/osm_bright/{z}/{x}/{y}{r}.png',
#                 options={
#                 'maxZoom': maxZoom,
#                 'minZoom': minZoom,
#                 'attribution': '&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
#                 },
#             )
#             # ui.label().bind_text_from(m, 'center', lambda center: f'Center: {center[0]:.3f}, {center[1]:.3f}')
#             # ui.label().bind_text_from(m, 'zoom', lambda zoom: f'Zoom: {zoom}')

#         with ui.card().classes("p-10"):
#             demo = Demo()

#             with ui.column().classes("w-full gap-4"):  # stack all vertically
#                 with ui.column().classes('w-full'):
#                     ui.label('Slider 1')
#                     ui.slider(min=1, max=10).set_value(3)

#                 with ui.column().classes('w-full'):
#                     ui.label('Slider 2')
#                     ui.slider(min=1, max=10).set_value(2)

#                 with ui.column().classes('w-full'):
#                     ui.label('Slider 3')
#                     ui.slider(min=1, max=10).set_value(8)

#                 with ui.column().classes('w-full'):
#                     ui.label('Bound Slider')
#                     ui.slider(min=1, max=3).bind_value(demo, 'number')

#                 with ui.column().classes('w-full'):
#                     ui.label('Toggle')
#                     ui.toggle({1: 'A', 2: 'B', 3: 'C'}).bind_value(demo, 'number')

#                 with ui.column().classes('w-full'):
#                     ui.label('Number')
#                     ui.number().bind_value(demo, 'number')


#     ui.run()

    