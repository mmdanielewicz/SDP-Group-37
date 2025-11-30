import streamlit as st
from backend_bridge import handle_user_query

st.set_page_config(page_title="Senior Design MVP", layout="wide")

st.title("Disaster Routing Assistant (MVP)")

st.write(
    "Ask a question about shelters, routes, or disasters."
)

st.subheader("Ask a question")
user_query = st.text_area(
    "Describe what you need:",
    placeholder="e.g., Find nearby shelters in Storrs, CT that are not in high flood risk zones.",
)

col1, col2 = st.columns(2)
with col1:
    start_location = st.text_input("Start location", "Storrs, CT")
with col2:
    mode = st.selectbox("Mode", ["Shelters nearby", "Safe route", "General question"])

if st.button("Run query"):
    if not user_query.strip():
        st.warning("Please type a question first.")
    else:
        with st.spinner("Calling backend orchestration..."):
            result = handle_user_query(user_query)

        st.write("### Query context")
        st.write("**Your query:**", user_query)
        st.write("**Start location (UI only for now):**", start_location)
        st.write("**Mode:**", mode)

        # Show backend result 
        if isinstance(result, dict):
            # 1) show shelters in a table
            shelter_results = result.get("shelter_results")
            if shelter_results and shelter_results.get("nearest_shelters"):
                shelters = shelter_results["nearest_shelters"]

                # Streamlit can take list-of-dicts directly
                st.subheader("Nearest shelters (MVP view)")
                st.write(
                    "Showing shelters returned by the Data Agent for the "
                    "hard-coded test location in CT."
                )

                # Pick the key fields to show
                nice_rows = []
                for s in shelters:
                    nice_rows.append({
                        "Name": s.get("name"),
                        "Address": f"{s.get('address', '')}, {s.get('city', '')}, {s.get('state', '')} {s.get('zip', '')}",
                        "Status": s.get("status"),
                        "Accessible": s.get("handicap_accessible"),
                        "Distance (mi)": round(s.get("straightline_distance_miles", 0), 2),
                    })

                st.dataframe(nice_rows, use_container_width=True)
            else:
                st.info("No shelter_results returned from backend.")

            # 2) show raw JSON for debugging / writeup
            st.subheader("Backend response (raw context)")
            st.json(result)
        else:
            st.subheader("Backend response (non-dict)")
            st.write(result)
