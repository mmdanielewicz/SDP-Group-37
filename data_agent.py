# data_agent.py
import os
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


class DataAgent:
    def __init__(self, base_path="data"):
        self.base_path = base_path

        # --- Load FEMA shapefile ---
        shp_path = os.path.join(base_path, "National_Shelter_System_Facilities.shp")
        if not os.path.exists(shp_path):
            raise FileNotFoundError(f"Shapefile not found at {shp_path}")

        self.df = gpd.read_file(shp_path)
        print(f"Loaded {len(self.df)} shelter points from FEMA dataset.")

        # --- Load supplemental CSV (if available) ---
        csv_path = os.path.join(base_path, "fema_shelters_clean.csv")
        if os.path.exists(csv_path):
            csv_df = pd.read_csv(csv_path)

            # normalize names to avoid mismatch
            csv_df["shelter_na"] = csv_df["shelter_na"].astype(str).str.strip().str.lower()
            self.df["shelter_na"] = self.df["shelter_na"].astype(str).str.strip().str.lower()

            # merge and fix geometry
            self.df = self.df.merge(csv_df, on="shelter_na", how="left", suffixes=("", "_csv"))
            if "geometry_x" in self.df.columns:
                self.df = self.df.rename(columns={"geometry_x": "geometry"})
            if "geometry_y" in self.df.columns:
                self.df = self.df.drop(columns=["geometry_y"])
            self.df = gpd.GeoDataFrame(self.df, geometry="geometry", crs="EPSG:4326")

        else:
            print("Warning: CSV not found — using shapefile only.")

    # -------------------------------------------------------------
    def get_nearest_shelters(self, lat, lon, limit=3, state_filter=None):
        """Find nearest shelters to a given coordinate."""

        user_point = Point(lon, lat)

        df_filtered = self.df
        if state_filter:
            df_filtered = df_filtered[df_filtered["state"].str.lower() == state_filter.lower()]

        # Reproject to planar coordinates for accurate distances
        df_proj = df_filtered.to_crs(epsg=3857)
        user_point_proj = gpd.GeoSeries([user_point], crs="EPSG:4326").to_crs(epsg=3857)[0]

        df_proj["distance_m"] = df_proj.geometry.distance(user_point_proj)
        df_proj["distance_miles"] = df_proj["distance_m"] / 1609.34

        nearest = df_proj.sort_values("distance_miles").head(limit)

        results = {
            "input_location": {"lat": lat, "lon": lon},
            "nearest_shelters": []
        }

        for _, row in nearest.iterrows():
            results["nearest_shelters"].append({
                "name": row.get("shelter_na", "Unknown").title() if row.get("shelter_na") else "Unknown",
                "address": row.get("address_1", "N/A"),
                "city": row.get("city", "N/A"),
                "state": row.get("state", "N/A"),
                "zip": str(row.get("zip", "")),
                "status": row.get("shelter_st", "Unknown"),
                "lat": row.geometry.y,
                "lon": row.geometry.x,
                "distance_miles": round(row.distance_miles, 2)
            })

        return results

    # -------------------------------------------------------------
    def handle_query(self, lat, lon, state=None):
        """Handle a query by coordinates."""
        data = self.get_nearest_shelters(lat, lon, limit=3, state_filter=state)
        print(json.dumps(data, indent=2))
        return data


# -------------------------------------------------------------
if __name__ == "__main__":
    agent = DataAgent(base_path="data")

    # Example usage: use direct coordinates
    agent.handle_query(lat=41.807, lon=-72.253, state="CT")
