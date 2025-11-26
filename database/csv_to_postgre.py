import pandas as pd
from sqlalchemy import create_engine

import pandas as pd
from sqlalchemy import create_engine

csv_path = r"C:\Users\arilo\OneDrive\Senior Design\Code\SDP-Group-37\data\processed\fema_shelters_clean.csv"
engine = create_engine("postgresql://postgres:password@localhost:5432/ct_disaster_resilience")

df = pd.read_csv(csv_path, low_memory=False)
df_ct.to_sql("fema_shelters_ct", engine, if_exists="replace", index=False)
