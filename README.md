# Frontend (Streamlit UI) – Senior Design MVP

The Streamlit app connects to the backend **Orchestration Agent**, which
classifies user queries using the LLM and calls the **Data Agent** and ***Routing Agent***, if the query requires routing.

---

##  How to Run the Frontend

### 1. Create and activate a virtual environment (first time only)
From the root of the repo:

```
python -m venv .venv
.\.venv\Scripts\activate
```

### 2. Install required packages
```
pip install -r requirements.txt
pip install streamlit
pip install ollama
pip install geopandas fiona shapely pyproj
```

### 3. Install and start Ollama
Make sure ollama is downloaded
```
ollama pull llama3.1:8b
```

### 4. Run Streamlit UI
From repo root:
```
python -m streamlit run frontend/app.py
```
The UI opens at: http://localhost:8501

