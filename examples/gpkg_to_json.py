import geopandas as gpd
import os
from pathlib import Path

# Set working directory
script_dir = Path(__file__).parent.resolve()
os.chdir(script_dir)

# Path to your file
gpkg_path = './data/rat_data.gpkg'

# Read the file
gdf = gpd.read_file(gpkg_path)
for col in gdf.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns:
    gdf[col] = gdf[col].astype(str)

# Convert the GeoDataFrame to a GeoJSON string
geojson_string = gdf.to_json()

# Print the string so you can copy it

# Or save it to a text file to open and copy
with open('data.json', 'w') as f:
    f.write(geojson_string)