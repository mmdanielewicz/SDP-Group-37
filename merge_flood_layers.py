import os
import pandas as pd
import geopandas as gpd

base_dir = "data/hazards"
merged = []

for county in os.listdir(base_dir):
    county_dir = os.path.join(base_dir, county)
    if os.path.isdir(county_dir):
        for file in os.listdir(county_dir):
            if file.endswith(".shp") and "S_FLD_HAZ_AR" in file:
                path = os.path.join(county_dir, file)
                print(f"Loading {path}")
                try:
                    gdf = gpd.read_file(path).to_crs("EPSG:4326")
                    gdf["county"] = county
                    merged.append(gdf)
                except Exception as e:
                    print(f"Error reading {path}: {e}")

if merged:
    print("Merging all counties...")
    full_state = gpd.GeoDataFrame(pd.concat(merged, ignore_index=True), crs="EPSG:4326")
    output_path = os.path.join(base_dir, "CT_Flood_Zones.shp")
    full_state.to_file(output_path)
    print(f"Merged flood hazard layer saved to {output_path}")
else:
    print("No shapefiles found to merge.")
