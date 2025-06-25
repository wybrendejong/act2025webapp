""""
# ACT
# webGUI
"""
import random
from nicegui import ui, html, app, events
import matplotlib.pyplot as plt
from fastapi.staticfiles import StaticFiles
import json
import geopandas as gpd
import folium
import pandas as pd
import branca.colormap as cm
from pathlib import Path
import os
from io import BytesIO

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
        try:
            self.upload_label.text = 'Uploading & Processing Rat Monitor Data in Progress...'
            file_bytes = BytesIO(e.content.read())
            rat_df = data_loading.load_rm_data(file_bytes)
            self.rat_gdf = data_loading.transform_to_spatiotemporal_gdf(rat_df, self.pc_gdf)

            self.clf = classification.train_classifier(self.rat_gdf)
            self.rat_proba_gdf = classification.predict_probabilities(self.rat_gdf, self.clf)

            self.reset_map_html()
        except Exception as ex:
            self.upload_label.text = f'Error: {str(ex)}'
            ui.notify(f'Error processing file: {str(ex)}', type='negative')
            raise

    def update_pc_ui(self, e: events.UiEventArguments):
        """Updates the graph based on the postal code input."""
        try:
            postal_code = int(e.value.strip())
            if not postal_code:
                self.graph_frame.content = ""
                return

            # # Filter the GeoDataFrame for the given postal code
            # filtered_gdf = self.rat_proba_gdf[self.rat_proba_gdf['postcode'] == postal_code]
            # print(f"Filtered data for postal code {postal_code}: {filtered_gdf.shape[0]} rows")
            # if filtered_gdf.empty:# # Filter the GeoDataFrame for the given postal code
            # filtered_gdf = self.rat_proba_gdf[self.rat_proba_gdf['postcode'] == postal_code]
            # print(f"Filtered data for postal code {postal_code}: {filtered_gdf.shape[0]} rows")
            # if filtered_gdf.empty:
            #     self.graph_frame.content = "No data available for this postal code."
            #     return

            # # Create a simple bar chart using the filtered data
            # fig = filtered_gdf.plot.bar(x='month', y='prob_positive', title=f'Rat Probability for {postal_code}')
            # fig.set_ylabel('Probability of Rat Sighting')
            # fig.set_xlabel('Month')

            # New section: Show historical sightings for the postal code
            if self.rat_gdf is None:
                self.graph_frame.content = "No historical data loaded."
                return

            historical_gdf = self.rat_gdf[self.rat_gdf['postcode'] == postal_code]
            print(f"Historical data for postal code {postal_code}: {historical_gdf.shape[0]} rows")
            if historical_gdf.empty:
                self.graph_frame.content = "No historical sightings for this postal code."
                return
            print(historical_gdf.head())

            # Create a bar chart of historical sightings per year
            

            historical_gdf.loc[:, 'month'] = pd.to_datetime(historical_gdf['month'], errors='coerce')
            # Group by year and sum the 'TOTAAL' column
            yearly_totals = historical_gdf.groupby(historical_gdf['month'].dt.year)['TOTAAL'].sum()
            fig, ax = plt.subplots()
            yearly_totals.plot(kind='bar', ax=ax)
            ax.set_title(f'Historical Rat Sightings per Year for {postal_code}')
            ax.set_xlabel('Year')
            ax.set_ylabel('Number of Sightings')
            #     self.graph_frame.content = "No data available for this postal code."
            #     return

            # # Create a simple bar chart using the filtered data
            # fig = filtered_gdf.plot.bar(x='month', y='prob_positive', title=f'Rat Probability for {postal_code}')
            # fig.set_ylabel('Probability of Rat Sighting')
            # fig.set_xlabel('Month')

            # New section: Show historical sightings for the postal code
            if self.rat_gdf is None:
                self.graph_frame.content = "No historical data loaded."
                return

            historical_gdf = self.rat_gdf[self.rat_gdf['postcode'] == postal_code]
            print(f"Historical data for postal code {postal_code}: {historical_gdf.shape[0]} rows")
            if historical_gdf.empty:
                self.graph_frame.content = "No historical sightings for this postal code."
                return

            # Create a bar chart of historical sightings per month

            monthly_counts = historical_gdf.groupby('month').size()
            fig, ax = plt.subplots()
            yearly_totals.plot(kind='bar', ax=ax)
            ax.set_title(f'Historical Rat Sightings for {postal_code}')
            ax.set_xlabel('Month')
            ax.set_ylabel('Number of Sightings')
            
            # Save the figure to a PNG image in memory and display it as HTML
            import base64
            from io import BytesIO
            buf = BytesIO()
            fig.get_figure().savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            html_str = f'<img src="data:image/png;base64,{img_base64}" style="width:100%;height:auto;" />'
            self.graph_frame.content = html_str
        except Exception as ex:
            self.graph_frame.content = f"Error generating graph: {str(ex)}"
            ui.notify(f'Error generating graph: {str(ex)}', type='negative')
            raise

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
            with ui.row():
                with ui.card().classes("w-full"):
                    with ui.column().classes("w-full gap-4"):

                        with ui.column().classes('w-full'):
                            self.upload_label = ui.label('Upload Rat Monitor Data:')
                            ui.upload(on_upload=self.upload_rm_file).props("accept=.xlsx").classes("max-w-full")

                        with ui.column().classes('w-full'):
                            ui.label('Show month in map:')
                            ui.toggle({1: '+1', 2: '+2', 3: '+3'})
                        with ui.column().classes('w-full'):
                            ui.label('postal code selection:')
                            self.postal_code_input = ui.input(on_change=self.update_pc_ui, label='Enter postal code', placeholder='e.g. 1234').classes('w-full')

                        with ui.column().classes('w-full'):
                            ui.label('Graph:')
                            self.graph_frame = ui.html("").classes('w-full h-64 rounded bg-white')

                        

    def run(self):
        ui.run()