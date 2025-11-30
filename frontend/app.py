# frontend/app.py
import streamlit as st
from backend_bridge import handle_user_query

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
    start_location = st.text_input("Start location", "Storrs, CT")
with col2:
    mode = st.selectbox("Mode", ["Shelters nearby", "Safe route", "General question"])

if st.button("Run query"):
    if not user_query.strip():
        st.warning("Please type a question first.")
    else:
        with st.spinner("Calling backend orchestration..."):
            result = handle_user_query(user_query)

        # --- Basic context ---
        st.write("### Query context")
        st.write("**Your query:**", user_query)
        st.write("**Start location (UI only for now):**", start_location)
        st.write("**Mode:**", mode)

        # --- Handle errors ---
        if isinstance(result, dict) and "error" in result:
            st.error(f"Backend error: {result['error']}")
            with st.expander("Raw backend response"):
                st.json(result)
        elif isinstance(result, dict):
            # --- Case 1: New combined result WITH ROUTES ---
            if "shelters" in result:
                st.subheader("Shelters with routing (from orchestration + routing agent)")

                shelters = result["shelters"]
                if not shelters:
                    st.info("No shelters returned by the backend.")
                else:
                    # Lightweight table of top shelters
                    rows = []
                    for s in shelters[:5]:
                        route = s.get("route")
                        distance_display = None
                        if route and "distance" in route:
                            distance_display = route["distance"].get("display")

                        rows.append({
                            "Name": s.get("name"),
                            "City": s.get("city"),
                            "State": s.get("state"),
                            "Status": s.get("status"),
                            "Accessible": s.get("handicap_accessible"),
                            "Straight-line (mi)": round(s.get("straightline_distance_miles", 0), 2),
                            "Route distance": distance_display,
                        })

                    st.table(rows)

                    # Show directions for the nearest shelter that has a route
                    nearest_with_route = next(
                        (s for s in shelters if s.get("route") is not None),
                        None
                    )

                    if nearest_with_route:
                        route = nearest_with_route["route"]
                        st.markdown(
                            f"#### Turn-by-turn directions "
                            f"to **{nearest_with_route['name']}**"
                        )

                        steps = route.get("directions", {}).get("steps", [])
                        if steps:
                            for step in steps:
                                st.write("•", step)
                        else:
                            st.info("No detailed steps returned in route.")

                    else:
                        st.info("No routing information found in the response.")

            # --- Case 2: Old shelter-only data agent result ---
            elif "shelter_results" in result and "nearest_shelters" in result["shelter_results"]:
                st.subheader("Nearest shelters (Data Agent only)")
                sr = result["shelter_results"]
                shelters = sr.get("nearest_shelters", [])

                if not shelters:
                    st.info("No shelters returned by Data Agent.")
                else:
                    rows = []
                    for s in shelters[:10]:
                        rows.append({
                            "Name": s.get("name"),
                            "City": s.get("city"),
                            "State": s.get("state"),
                            "Status": s.get("status"),
                            "Accessible": s.get("handicap_accessible"),
                            "Distance (mi)": round(s.get("straightline_distance_miles", 0), 2),
                        })
                    st.table(rows)

            # --- Case 3: Raw data agent (no orchestration) ---
            elif "nearest_shelters" in result:
                st.subheader("Nearest shelters (raw Data Agent output)")
                shelters = result.get("nearest_shelters", [])
                rows = []
                for s in shelters[:10]:
                    rows.append({
                        "Name": s.get("name"),
                        "City": s.get("city"),
                        "State": s.get("state"),
                        "Status": s.get("status"),
                        "Accessible": s.get("handicap_accessible"),
                        "Distance (mi)": round(s.get("straightline_distance_miles", 0), 2),
                    })
                st.table(rows)

            # --- Fallback: unknown structure ---
            else:
                st.info("Backend returned data in an unexpected format. See raw JSON below.")

            # Always let people inspect the raw response
            with st.expander("Raw backend response (JSON)"):
                st.json(result)

        else:
            # Non-dict edge case
            st.subheader("Backend response (non-dict)")
            st.write(result)
