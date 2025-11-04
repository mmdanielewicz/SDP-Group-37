import geopandas as gpd  
from pathlib import Path  

path = Path(r"C:\Users\arilo\OneDrive\Senior Design\Code\SDP-Group-37\data\raw")

gdf = gpd.read_file(path)

output_path = Path(r"C:\Users\arilo\OneDrive\Senior Design\Code\SDP-Group-37\data\processed/fema_shelters_clean.csv")
gdf.to_csv(output_path, index=False)