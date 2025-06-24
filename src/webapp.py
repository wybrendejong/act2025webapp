""""
# ACT
# webGUI
"""
import random
from nicegui import ui, html, app, events
from fastapi.staticfiles import StaticFiles
import json
import geopandas as gpd
import folium
import pandas as pd
import branca.colormap as cm
from pathlib import Path
import os

from src import mapping, data_loading, classification

pc_gpkg_path = "data/cbs_pc4_2024_v1.gpkg"


class WebApp():
    def __init__(self):
        self.clf = None
        self.rat_gdf = None
        self.rat_proba_gdf = None

        self.mount_dirs()
        self.build_ui()
        self.reset_map_html()

        self.pc_gdf = data_loading.load_pc_geodata(pc_gpkg_path)


    def mount_dirs(self):
        if not os.path.exists('map'):
            os.makedirs('map')
        if not os.path.exists('data'):
            os.makedirs('data')
        
        app.mount("/map", StaticFiles(directory="map"), name="map")


    def upload_rm_file(self, e: events.UploadEventArguments):
        self.upload_label.text = 'Uploading & Processing Rat Monitor Data in Progress...'
        
        rat_df = data_loading.load_rm_data(e.content)
        self.rat_gdf = data_loading.transform_to_spatiotemporal_gdf(rat_df, self.pc_gdf)

        self.clf = classification.train_classifier(self.rat_gdf)
        self.rat_proba_gdf = classification.predict_probabilities(self.rat_gdf, self.clf)

        self.reset_map_html()


    def reset_map_html(self):

        if self.rat_proba_gdf is not None:
            m = mapping.update_map(self.rat_proba_gdf)
        else:
            m = mapping.empty_map()

        m.save('./map/map.html')

        cache_buster = random.randint(0, int(1e9))
        self.map_frame.content = f"""
        <div style="position: relative; width: 100%; padding-top: 55%;">
            <iframe src="./map/map.html?cb={cache_buster}"
                    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none;"
                    loading="lazy"
                    referrerpolicy="no-referrer-when-downgrade">
            </iframe>
        </div>
        """

        self.upload_label.text = 'Upload Rat Monitor Data:'


    def build_ui(self):

        with ui.grid().classes('grid grid-cols-1 md:grid-cols-[3fr_1fr] w-full gap-5'):
            with ui.card().classes('w-full'):
                ui.markdown('## Rat Monitor Future Predictions')
                self.map_frame = ui.html("").classes('w-full')

            with ui.card().classes("p-10"):
                with ui.column().classes("w-full gap-4"):

                    with ui.column().classes('w-full'):
                        self.upload_label = ui.label('Upload Rat Monitor Data:')
                        ui.upload(on_upload=self.upload_rm_file).props("accept=.xlsx").classes("max-w-full")

                    with ui.column().classes('w-full'):
                        ui.label('Show month in map:')
                        ui.toggle({1: '+1', 2: '+2', 3: '+3'})


    def run(self):
        ui.run()