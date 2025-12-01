# frontend/app.py
import streamlit as st
from backend_bridge import handle_user_query, guess_location, get_coords

st.set_page_config(page_title="Senior Design MVP", layout="wide")

st.title("Disaster Routing Assistant (MVP)")

st.write(
    "This MVP UI is connected to the orchestration agent. "
    "Ask a question about shelters, routes, or disasters."
)

st.subheader("Ask a question")
user_query = st.text_area(
    "Describe what you need:",
    placeholder="e.g., Find nearby shelters in Storrs, CT that are not in high flood risk zones.",
)

col1, col2 = st.columns(2)
with col1:
    #autofills with location based on IP address
    start_location = st.text_input("Start location", guess_location())
with col2:
    mode = st.selectbox("Mode", ["Shelters nearby", "Safe route", "General question"])

if st.button("Run query"):
    coords=get_coords(start_location)
    if not user_query.strip():
        st.warning("Please type a question first.")
    elif not coords:
        st.warning("Location name not recognized.")
    else:
        with st.spinner("Calling backend orchestration..."):
            print(coords)
            result = handle_user_query(user_query,coords[0],coords[1])

        st.write("### Query context")
        st.write("**Your query:**", user_query)
        st.write("**Start location:**", start_location)
        st.write("**Mode:**", mode)

        # Handle the response
        if isinstance(result, dict):
            if "error" in result:
                st.error(f"Backend error: {result['error']}")
                st.json(result)
            elif "response" in result:
                # NEW: Show natural language response from response agent
                st.subheader("Response")
                st.markdown(result["response"])
                
                # Show raw data in expandable section
                with st.expander("View technical details"):
                    st.json(result["raw_data"])
            else:
                # Fallback for old format without response agent
                st.subheader("Backend response")
                st.json(result)
        else:
            st.subheader("Backend response (non-dict)")
            st.write(result)