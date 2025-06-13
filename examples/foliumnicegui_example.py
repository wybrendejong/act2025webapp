from nicegui import ui, html, app
from fastapi.staticfiles import StaticFiles
import json
import geopandas as gpd
import folium
import pandas as pd
import branca.colormap as cm
from pathlib import Path
import os

# Set working directory
script_dir = Path(__file__).parent.resolve()
os.chdir(script_dir)

# mount /map directory to make nicegui reach for the map.html file
app.mount("/map", StaticFiles(directory="map"), name="map")
def mapSetup():
    # Load your GeoDataFrame
        rat_gdf = gpd.read_file("./data/rat_data.gpkg", layer="my_layer")
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

        m = folium.Map(location=center, zoom_start=9)

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
        m.save("./map/map.html")





with ui.grid().classes('grid grid-cols-1 md:grid-cols-[3fr_1fr] w-full gap-5'):
    with ui.card():
        with ui.card().tight():
            ui.html(f"""
                <iframe src="./map/map.html"
                        style="width: 100%; height: 500px; border: none;"
                        loading="lazy"
                        referrerpolicy="no-referrer-when-downgrade">
                </iframe>
            """)
        style = 'width: 80%; height: 80%; margin: 20px auto; border: 1px solid #ccc;'
        mapSetup()
        
ui.run()