# data_agent.py
import os
import json
import pandas as pd
import geopandas as gpd
from pyproj import Geod
from shapely.geometry import Point

class DataAgent:

    geod = Geod(ellps="WGS84")  #initialize once for true Earth distances

    @staticmethod
    def _mi(meters: float) -> float:
        """Convert meters to miles"""
        return meters / 1609.34
    

    def __init__(self, base_path="data"):
        self.base_path = base_path

        # --- Load FEMA shapefile ---
        shp_path = os.path.join(base_path, "National_Shelter_System_Facilities.shp")
        if not os.path.exists(shp_path):
            raise FileNotFoundError(f"Shapefile not found at {shp_path}")

        self.df = gpd.read_file(shp_path)
        print(f"Loaded {len(self.df)} shelter points from FEMA dataset.")

        # Clean up common typos in names
        self.df["shelter_na"] = self.df["shelter_na"].astype(str).apply(self.clean_text)

        # --- Load FEMA Flood Hazard Layer ---
        hazard_path = os.path.join(base_path, "hazards", "floods", "CT_Flood_Zones.shp")
        if os.path.exists(hazard_path):
            self.hazards = {
                "fema_flood": gpd.read_file(hazard_path).to_crs("EPSG:4326")
            }
            print(f"Loaded {len(self.hazards['fema_flood'])} FEMA flood polygons for Connecticut.")
        else:
            print("FEMA flood hazard shapefile not found.")



        # --- Load supplemental CSV (if available) ---
        csv_path = os.path.join(base_path, "fema_shelters_clean.csv")
        if os.path.exists(csv_path):
            csv_df = pd.read_csv(csv_path)

            # Normalize names to avoid mismatch
            csv_df["shelter_na"] = csv_df["shelter_na"].astype(str).str.strip().str.lower()
            self.df["shelter_na"] = self.df["shelter_na"].astype(str).str.strip().str.lower()

            # Merge and fix geometry
            self.df = self.df.merge(csv_df, on="shelter_na", how="left", suffixes=("", "_csv"))
            self.df = (
                self.df.rename(columns={"geometry_x": "geometry"}, errors="ignore")
                        .drop(columns=["geometry_y"], errors="ignore")
            )
            self.df = gpd.GeoDataFrame(self.df, geometry="geometry", crs="EPSG:4326")

            # Wheelchair accessibility logic setup
            if "wheelchair" in self.df.columns:
                self.df["handicap_accessible"] = self.df["wheelchair"].apply(
                    lambda x: "Yes"
                    if str(x).strip().lower() in ["yes", "y", "true", "1", "available", "accessible"]
                    else "No"
                )
            else:
                self.df["handicap_accessible"] = "No"

        else:
            print("Warning: CSV not found — using shapefile only.")
            self.df["handicap_accessible"] = None

    # -----------------------------------------------------
    def clean_text(self, text):
        """Fix common typos and spacing in shelter names"""
        if not isinstance(text, str):
            return text
        text = text.strip()
        text = text.replace("Univercity", "University")
        text = text.replace("Connecticuit", "Connecticut")
        return text
    

    # -------------------------------------------------------------------
    def _dedupe_by_name_city(self, df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Collapse records that look like the same shelter (same name+city+state),
        keeping the one that is closest to the user (smallest distance_miles).

        Assumes df already has a 'distance_miles' column.
        """
        if df.empty:
            return df

        tmp = df.copy()

        # Normalize for grouping (re-use your existing text cleaner)
        tmp["name_norm"] = tmp["name"].fillna("").map(self._normalize_text)
        tmp["city_norm"] = tmp["city"].fillna("").map(self._normalize_text)

        # Make sure closest shelters come first
        tmp = tmp.sort_values("distance_miles")

        # Group by normalized name + city + state, keep the first (closest) row
        grouped = tmp.groupby(["name_norm", "city_norm", "state"], as_index=False, sort=False).first()

        # Drop helper columns
        return grouped.drop(columns=["name_norm", "city_norm"])

    
    #-----------------------------------------------------
    @staticmethod
    def classify_flood_risk(zone: str, subtype: str = "", sfha_tf=None) -> str:
        """
        Map FEMA fields to a simple risk label.
        - SFHA (A/V zones) => High
        - Zone X shaded (0.2% annual chance) => Moderate
        - Zone X unshaded => Low
        """
        z = (zone or "").upper().strip()
        st = (subtype or "").upper()
        sfha_flag = str(sfha_tf).upper() in {"T", "Y", "1", "TRUE", "YES"}

        if sfha_flag or z.startswith(("A", "V")):
            return "High"
        if z == "X" and ("0.2" in st or "0.2 PCT" in st or "SHADED" in st):
            return "Moderate"
        if z == "X":
            return "Low"
        return "Unknown"



    # -------------------------------------------------------------
    def get_nearest_shelters(self, lat, lon, limit=3, state_filter=None):
        """Find nearest shelters using true geodesic distance (WGS84)."""

        df_filtered = self.df
        if state_filter and "state" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["state"].str.lower() == state_filter.lower()]

        # Geodesic distance calculation
        def dist_miles(point):
            _, _, meters = self.geod.inv(lon, lat, float(point.x), float(point.y))
            return self._mi(meters)

        df_filtered = df_filtered.copy()
        df_filtered["distance_miles"] = df_filtered.geometry.apply(dist_miles)
        nearest = df_filtered.nsmallest(limit, "distance_miles")

        # Build a normalized dedup key (name + city + state)
        df_filtered["_dedup_key"] = (
            df_filtered["shelter_na"].fillna("").str.strip().str.lower() + "|" +
            df_filtered["city"].fillna("").str.strip().str.lower() + "|" +
            df_filtered["state"].fillna("").str.strip().str.lower()
        )

        # Sort so closest always wins first
        df_filtered = df_filtered.sort_values("distance_miles", ascending=True)

        # Drop duplicates using normalized key but keep closest record
        df_filtered = df_filtered.drop_duplicates(subset="_dedup_key", keep="first")

        # Now select final nearest shelters
        nearest = df_filtered.head(limit)

        # Cleanup temp column
        df_filtered = df_filtered.drop(columns=["_dedup_key"])

        results = {
            "input_location": {"lat": lat, "lon": lon},
            "nearest_shelters": []
        }

        for _, row in nearest.iterrows():

            hazards_here = []

            if hasattr(self, "hazards"):
                shelter_gdf = gpd.GeoDataFrame(geometry=[row.geometry], crs="EPSG:4326")
                for hname, hdf in self.hazards.items():
                    joined = gpd.sjoin(shelter_gdf, hdf, predicate="intersects", how="inner")
                    if not joined.empty:
                        rec = joined.iloc[0]
                        zone = rec.get("FLD_ZONE", "Unknown")
                        subtype = rec.get("ZONE_SUBTY", "")
                        sfha_tf = rec.get("SFHA_TF", None)

                        risk = self.classify_flood_risk(zone, subtype, sfha_tf)

                        hazards_here.append({
                            "type": hname,           # e.g., "fema_flood"
                            "zone": zone,            # e.g., "AE", "VE", "X"
                            "risk": risk             # e.g., "High", "Moderate", "Low"
                        })



            results["nearest_shelters"].append({
                "name": row.get("shelter_na", "Unknown").title() if row.get("shelter_na") else "Unknown",
                "address": row.get("address_1", "N/A"),
                "city": row.get("city", "N/A"),
                "state": row.get("state", "N/A"),
                "zip": str(row.get("zip", "")),
                "status": row.get("shelter_st", "Unknown"),
                "lat": row.geometry.y,
                "lon": row.geometry.x,
                "straightline_distance_miles": round(row.distance_miles, 2),
                "handicap_accessible": row.get("handicap_accessible", "No"),
                "hazard_polygons": hazards_here or None
            })

        return results



    # -------------------------------------------------------------
    def handle_query(self, lat, lon, state=None):
        """Handle a query by coordinates."""
        data = self.get_nearest_shelters(lat, lon, limit=20, state_filter=state)
        #print(json.dumps(data, indent=2))
        return data


# -------------------------------------------------------------
if __name__ == "__main__":
    agent = DataAgent(base_path="data")

    # Example usage: use direct coordinates
    agent.handle_query(lat=41.2940, lon=-72.3768, state="CT")
