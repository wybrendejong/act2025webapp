""""
# ACT
# webGUI
"""
import matplotlib
import pyogrio
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import random
from nicegui import ui, html, app, events
from fastapi.staticfiles import StaticFiles
import json
import geopandas as gpd
import pandas as pd
import branca.colormap as cm
from pathlib import Path
import os
from io import BytesIO
import matplotlib
import base64

from src import mapping, data_loading, classification

pc_gpkg_path = "data/cbs_pc4_2024_v1.gpkg"
map_html_path = "./map/map.html"
rat_gdf_path = "./data/rat_gdf.gpkg"
rat_proba_gdf_path = "./data/rat_proba_gdf.gpkg"


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
        app.mount("/data", StaticFiles(directory="data"), name="data")

        if os.path.exists(rat_gdf_path) and os.path.exists(rat_proba_gdf_path):
            try:
                self.rat_gdf = gpd.read_file(rat_gdf_path)
                self.rat_proba_gdf = gpd.read_file(rat_proba_gdf_path)
            except:
                ui.notify("Error loading data from previous session, please upload the data again.", type='negative')


    def upload_rm_file(self, e: events.UploadEventArguments):
        # Try to read and transform the uploaded data
        try:
            file_bytes = BytesIO(e.content.read())
            rat_df = data_loading.load_rm_data(file_bytes)
            self.rat_gdf = data_loading.transform_to_spatiotemporal_gdf(rat_df, self.pc_gdf)
            
        # Raise an exception and notify the user when uploading fails
        except Exception as e:
            ui.notify(f'Error processing file: {str(e)}', type='negative')
            raise

        # Train the classifier and update map with predictions
        else:
            self.clf = classification.train_classifier(self.rat_gdf)
            self.rat_proba_gdf = classification.predict_probabilities(self.rat_gdf, self.clf)

            self.rat_gdf.to_file(rat_gdf_path, driver='GPKG')
            self.rat_proba_gdf.to_file(rat_proba_gdf_path, driver='GPKG')

            self.graph_frame.content = ""
            self.reset_map_html()


    def update_pc_ui(self, e: events.UiEventArguments):
        # Retrieve postal code and check if it is valid
        postal_code = e.value.strip()
        
        if not postal_code:
            return
        if len(postal_code) < 4 or not postal_code.isnumeric():
            return
        
        postal_code = int(postal_code[:4])

        # Check if rat data is available and if it includes the postal code
        if self.rat_proba_gdf is None:
            ui.notify(f'No data uploaded yet', type='negative')
            return
        
        if postal_code not in self.rat_proba_gdf['postcode'].values:
            ui.notify(f'Postal code area {postal_code} not found', type='negative')
            return

        # Retrieve data of postal code
        probability = self.rat_proba_gdf.loc[self.rat_proba_gdf['postcode'] == postal_code, 'prob_positive'].values[0]
        historic_df = self.rat_gdf[self.rat_gdf['postcode'] == postal_code] 

        # Display postal code and probability
        self.postal_code_label.text = f"Postal code area: {postal_code}" 
        self.proba_label.text = f"Probability of rats being present: {probability:.2%}"

        # Plot the historical rat sightings for the past year
        fig, ax = plt.subplots(figsize=(6, 3))
        historic_df = historic_df.sort_values('month').tail(12)
        ax.bar(historic_df['month'], historic_df['TOTAAL'], width = pd.Timedelta(30, 'days'))
        ax.set_xlabel('Month')
        ax.set_ylabel('TOTAAL')
        ax.set_title(f"Rat Sightings for Postal Code {postal_code} in the previous 12 months")
        ax.set_ylim(bottom=0)
        plt.tight_layout()

        print(historic_df)

        # Write the plot to an IO buffer and display it in the graph frame
        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        self.graph_frame.content = f'<img src="data:image/png;base64,{img_base64}" style="width:100%;height:auto;" />'


    def reset_map_html(self):

        if self.rat_proba_gdf is not None:
            m = mapping.update_map(self.rat_proba_gdf)
        else:
            m = mapping.empty_map()
        
        m.save(map_html_path)

        cache_buster = random.randint(0, int(1e9))
        self.map_frame.content = f"""
        <div style="position: relative; width: 100%; padding-top: 50%;">
            <iframe src="./map/map.html?cb={cache_buster}"
                    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none;"
                    loading="lazy"
                    referrerpolicy="no-referrer-when-downgrade">
            </iframe>
        </div>
        """

        self.upload_label.text = 'Upload Rat Monitor Data:'
        self.month_label.text = f'Inspecting predictions for {self.rat_proba_gdf['month'].max():%m/%Y}'


    def build_ui(self):
        # Create Grid with 2 columns
        with ui.grid().classes('grid grid-cols-1 md:grid-cols-[3fr_1fr] w-full gap-5'):
            # Map Card
            with ui.card().classes('w-full'):
                ui.markdown('## Rat Monitor Future Predictions')
                self.map_frame = ui.html("").classes('w-full')

            # Interface Row
            with ui.row():
                with ui.card().classes("w-full"):
                    with ui.column().classes("w-full gap-4"):

                        with ui.column().classes('w-full'):
                            if self.rat_proba_gdf is not None:
                                self.month_label = ui.label('Loading predictions')
                            else:
                                self.month_label = ui.label('Upload rat data to inspect predictions')

                            self.postal_code_input = ui.input(on_change=self.update_pc_ui, label='Enter postal code', placeholder='e.g. 1234').classes('w-full')

                            self.postal_code_label = ui.label('Postcode: ')
                            self.proba_label = ui.label('Probability of rats being present: ')

                            ui.label('Historical data: ')
                            self.graph_frame = ui.html("").classes('w-full h-64 rounded bg-white')

                        with ui.column().classes('w-full'):
                            self.upload_label = ui.label('Upload rat monitor data:')
                            ui.upload(on_upload=self.upload_rm_file).props("accept=.xlsx").classes("max-w-full")
                        

    def run(self):
        ui.run()