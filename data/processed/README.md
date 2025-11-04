This folder contains processed data files derived from the raw FEMA National Shelter System Facilities shapefile.

Notes:
- **fema_shelters_clean.csv**: cleaned, includes CT shelters only.
- Columns include facility name, address, city, state, capacity, and other attributes.

## Querying the CSV

```python
import pandas as pd

# Load the CT FEMA shelters data
df = pd.read_csv("data/processed/fema_shelters_cleaned.csv")

# Example query: list the first 5 shelters in Hartford that are wheelchair accessible
result = df[(df["city"] == "HARTFORD") & (df["wheelchair"] == "YES")][
    ["facility_name", "city", "state", "capacity", "wheelchair"]
]
print(result.head())
