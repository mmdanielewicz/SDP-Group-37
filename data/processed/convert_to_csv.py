import geopandas as gpd  
from pathlib import Path  

path = Path(r"C:\Users\arilo\OneDrive\Senior Design\Code\SDP-Group-37\data\raw")

gdf = gpd.read_file(path)
gdf_ct = gdf[gdf["state"] == "CT"]

output_path = Path(r"C:\Users\arilo\OneDrive\Senior Design\Code\SDP-Group-37\data\processed/fema_shelters_clean.csv")
gdf_ct.to_csv(output_path, index=False)