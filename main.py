from nicegui import ui, html, app
from fastapi.staticfiles import StaticFiles
import json
import sys
import geopandas as gpd
import folium
import pandas as pd
import branca.colormap as cm
from pathlib import Path
import os
import src as funcs # type: ignore




# Set working directory
script_dir = Path(__file__).parent.resolve()
os.chdir(script_dir)




funcs.scriptInit()


gpkg_path = "./data/rat_data.gpkg"
maxZoom = 13
minZoom = 8

class Demo:
    def __init__(self):
        self.number = 1

with ui.grid().classes('grid; grid-cols-1 md:grid-cols-[3fr_1fr] w-full gap-5'):
    with ui.card():
        ui.html("<b>Rat Monitor</b>").style('font-size: 24pt')
    with ui.card():
        dark = ui.dark_mode()
        ui.switch('Dark mode').bind_value(dark)

with ui.grid().classes('grid grid-cols-1 md:grid-cols-[3fr_1fr] w-full gap-5'):
    with ui.card().tight():
        width = 1400
        height = 800
        ui.html(funcs.mapSetup(gpkg_path, width, height))


    with ui.card().classes("p-10"):
        demo = Demo()

        with ui.column().classes("w-full gap-4"):  # stack all vertically
            with ui.column().classes('w-full'):
                ui.label('Slider 1')
                ui.slider(min=1, max=10).set_value(3)

            with ui.column().classes('w-full'):
                ui.label('Slider 2')
                ui.slider(min=1, max=10).set_value(2)

            with ui.column().classes('w-full'):
                ui.label('Slider 3')
                ui.slider(min=1, max=10).set_value(8)

            with ui.column().classes('w-full'):
                ui.label('Bound Slider')
                ui.slider(min=1, max=3).bind_value(demo, 'number')

            with ui.column().classes('w-full'):
                ui.label('Toggle')
                ui.toggle({1: 'A', 2: 'B', 3: 'C'}).bind_value(demo, 'number')

            with ui.column().classes('w-full'):
                ui.label('Number')
                ui.number().bind_value(demo, 'number')


ui.run()

# print("Working directory:", os.getcwd())
# print("Sys path:", sys.path)
