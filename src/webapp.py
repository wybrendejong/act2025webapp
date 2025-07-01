""""
# ACT
# webGUI
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import random
from nicegui import ui, app, events
from fastapi.staticfiles import StaticFiles
import json
import geopandas as gpd
import pandas as pd
import os
from io import BytesIO
import matplotlib
import base64

from src import mapping, data_loading, classification

# Data paths
pc_gpkg_path = "data/cbs_pc4_2024_v1.gpkg"
map_html_path = "./map/map.html"
rat_gdf_path = "./data/rat_gdf.gpkg"
rat_proba_gdf_path = "./data/rat_proba_gdf.gpkg"
metrics_path = "./data/metrics.json"

# Predefined texts
recall_label_text = 'Percentage of areas that actually have rats and are predicted to have rats: '
precision_label_text = 'Percentage of areas predicted to have rats that actually have rats: '
accuracy_info_text = """
    The model that predicts the probabilities in the map was trained and evaluated on the rat monitor data that was uploaded
    to this website. The percentages shown above represent the accuracy of the model. 20% of the data was not used in training, 
    but was used to calculate these accuracy metrics. The model makes predictions for this subset of the data which is then 
    compared to the actual numbers.\n\n 
    These metrics describe how well the model performs in detecting areas with rats present. 
    The first metric evaluates the ability of the model to find all areas that actually have rats. It is assesed by how 
    many areas that actually have rats in the data were also predicted with a high probability of having rats. The second metric
    describes the precision of the model. It is assesesed by how many areas predicted with a high probability of having rats, 
    actually turned out to have rats in the data. 
"""

class WebApp():
    def __init__(self):
        # Initiliaze properties
        self.clf = None
        self.precision = None
        self.recall = None
        self.rat_gdf = None
        self.rat_proba_gdf = None

        # Load PC4 area geometries
        self.pc_gdf = data_loading.load_pc_geodata(pc_gpkg_path)

        # Mount the directories and prepare the UI
        self.mount_dirs()
        self.build_ui()
        self.reset_map_html()


    def mount_dirs(self):
        """
        Creates map and data directoris if they don't exist and mounts them for static files. 
        Also tries to load saved rat monitor data if it exists in the data directory.
        """
        if not os.path.exists('map'):
            os.makedirs('map')
        if not os.path.exists('data'):
            os.makedirs('data')

        # Mount static directories
        # Updating files in these directories won't trigger the webapp to restart
        app.mount("/map", StaticFiles(directory="map"), name="map")
        app.mount("/data", StaticFiles(directory="data"), name="data")

        # If saved data exists, attempt to load it
        if os.path.exists(rat_gdf_path) and os.path.exists(rat_proba_gdf_path) and os.path.exists(metrics_path):
            try:
                # Load rat monitor and prediction data
                self.rat_gdf = gpd.read_file(rat_gdf_path)
                self.rat_proba_gdf = gpd.read_file(rat_proba_gdf_path)

                # Load mtrics
                with open(metrics_path, 'r') as file:
                    metrics = json.load(file)
                    self.precision = metrics.get('precision')
                    self.recall = metrics.get('recall')

            except Exception as ex:
                ui.notify("Error loading data from previous session, please upload the data again.", type='negative')
                print(ex)


    def upload_rm_file(self, e: events.UploadEventArguments):
        """
        Event listener for file uploading. 

        Tries to load rat data from the uploaded file.
        If data loading is succesful, trains the classifier and generates predictions for the upcomig month.
        Saves the loaded data and the predictions in the data directory.
        """
        try:    
            # Try to read and transform the uploaded data    
            file_bytes = BytesIO(e.content.read())
            rat_df = data_loading.load_rm_data(file_bytes)
            self.rat_gdf = data_loading.transform_to_spatiotemporal_gdf(rat_df, self.pc_gdf)

        except Exception as ex:   
            # Print the exception and notify the user when uploading fails
            ui.notify(f'Error processing file: {str(ex)}', type='negative')
            print(ex)

        else:
            # Train tshe classifier and update map with predictions
            self.clf, self.precision, self.recall = classification.train_classifier(self.rat_gdf)
            self.rat_proba_gdf = classification.predict_probabilities(self.rat_gdf, self.clf)

            # Save the rat data and predictions for loading on future start ups
            self.rat_gdf.to_file(rat_gdf_path, driver='GPKG')
            self.rat_proba_gdf.to_file(rat_proba_gdf_path, driver='GPKG')

            # Save precision and recall scores to a file as well
            with open(metrics_path, 'w') as file:
                json.dump({'precision': float(self.precision), 'recall': float(self.recall)}, file)

            # Reset the ui contents
            self.graph_frame.content = ""
            self.reset_map_html()


    def update_pc_ui(self, e: events.UiEventArguments):
        """
        Event listener for postal code input.

        If the postal code in the input field is a valid PC4 postal codee, 
        retrieves and displays historical and prediction data for the postal code.
        """
        postal_code = e.value.strip()
        
        # Check if postal code is valid
        if not postal_code:
            return
        if len(postal_code) < 3 or not postal_code.isnumeric():
            return
        
        # Only retrieve the first 4 characters if the input is longer
        postal_code = int(postal_code[:4]) if len(postal_code) > 4 else int(postal_code)

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

        # Write the plot to an IO buffer and display it in the graph frame
        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        self.graph_frame.content = f'<img src="data:image/png;base64,{img_base64}" style="width:100%;height:auto;" />'


    def reset_map_html(self):
        """Resets the map html element based on the rat monitor data. Creates an empty map if the data is absent."""
        if self.rat_proba_gdf is not None:
            m = mapping.update_map(self.rat_proba_gdf)
        else:
            m = mapping.empty_map()
        
        m.save(map_html_path)

        # Use a cache buster to force the html element to reload
        cache_buster = random.randint(0, int(1e9))
        self.map_frame.content = f"""
        <div style="position: relative; width: 100%; padding-top: 50%;">
            <iframe src="{map_html_path}?cb={cache_buster}"
                    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none;"
                    loading="lazy"
                    referrerpolicy="no-referrer-when-downgrade">
            </iframe>
        </div>
        """

        # Update labels
        self.upload_label.text = 'Upload new Rat Monitor data:'

        if self.rat_proba_gdf is not None:
            self.month_label.text = f'Inspecting predictions for {self.rat_proba_gdf['month'].max():%m/%Y}'
        
        if self.precision is not None and self.recall is not None:
            self.precision_label.text = f'{precision_label_text}{self.precision:.1%}'
            self.recall_label.text = f'{recall_label_text}{self.recall:.1%}'



    def build_ui(self):
        """Builds the web UI using a grid with 2 rows: a map and an interface."""
        with ui.grid().classes('grid grid-cols-1 md:grid-cols-[3fr_1fr] w-full gap-5'):

            # Card for the map
            with ui.card().classes('w-full'):
                ui.markdown('## Rat Monitor Future Predictions')
                self.map_frame = ui.html("").classes('w-full')

            # Row for the interface
            with ui.row():
                with ui.card().classes("w-full"):
                    with ui.column().classes("w-full gap-4"):

                        # Data inspection section
                        with ui.column().classes('w-full'):
                            self.month_label = ui.label('Upload rat data to inspect predictions')
                            self.month_label.tailwind.font_weight('extrabold')

                            self.postal_code_input = ui.input(on_change=self.update_pc_ui, label='Enter postal code', placeholder='e.g. 1234').classes('w-full')

                            self.postal_code_label = ui.label('Postcode: ')
                            self.proba_label = ui.label('Probability of rats being present: ')

                            ui.label('Historical data: ')
                            self.graph_frame = ui.html("").classes('w-full h-32x rounded bg-white')

                        # Dialog with info about the accuracy metrics
                        with ui.dialog() as accuracy_dialog, ui.card():
                            ui.label(accuracy_info_text)
                            ui.button('Close', on_click=accuracy_dialog.close)

                        # Model performance section
                        with ui.column().classes('w-full'):
                            ui.label('Model performance:').tailwind.font_weight('extrabold')

                            self.recall_label = ui.label(recall_label_text)
                            self.precision_label = ui.label(precision_label_text)

                            ui.button(icon='help_outline', on_click=accuracy_dialog.open).tooltip('What do these metric mean?')

                        # File upload section
                        with ui.column().classes('w-full'):
                            self.upload_label = ui.label('Upload rat monitor data:')
                            self.upload_label.tailwind.font_weight('extrabold')

                            ui.upload(on_upload=self.upload_rm_file).props("accept=.xlsx").classes("max-w-full")
                        

    def run(self):
        ui.run()