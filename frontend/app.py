import streamlit as st
from streamlit_folium import folium_static
import folium
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
    start_location = st.text_input("Start location", guess_location())
with col2:
    mode = st.selectbox("Mode", ["Shelters nearby", "Safe route", "General question"])

if st.button("Run query"):
    coords = get_coords(start_location)

    if not user_query.strip():
        st.warning("Please type a question first.")
    elif not coords:
        st.warning("Location name not recognized.")
    else:
        with st.spinner("Calling backend orchestration..."):
            result = handle_user_query(user_query, coords[0], coords[1])

        st.write("### Query context")
        st.write("**Your query:**", user_query)
        st.write("**Start location:**", start_location)
        st.write("**Mode:**", mode)

        if isinstance(result, dict):
            if "error" in result:
                st.error(f"Backend error: {result['error']}")
                st.json(result)

            elif "response" in result:
                st.subheader("Response")
                st.markdown(result["response"])

                raw_data = result.get("raw_data", {})

                # render folium map if there's routing involved
                if "shelters" in raw_data and raw_data["shelters"]:
                    st.subheader("Map View")

                    user_lat = raw_data["user_location"]["lat"]
                    user_lon = raw_data["user_location"]["lon"]

                    m = folium.Map(location=[user_lat, user_lon], zoom_start=13)

                    folium.Marker(
                        [user_lat, user_lon],
                        popup="Your Location",
                        icon=folium.Icon(color="blue", icon="user", prefix="fa")
                    ).add_to(m)

                    colors = ['red', 'green', 'purple', 'orange', 'darkred']

                    for idx, shelter in enumerate(raw_data["shelters"][:5]):
                        slat = shelter["location"]["lat"]
                        slon = shelter["location"]["lon"]
                        color = colors[idx % len(colors)]

                        popup_html = f"""
                            <b>{shelter['name']}</b><br>
                            {shelter['address']}<br>
                            {shelter['city']}, {shelter['state']} {shelter['zip']}<br>
                            Status: {shelter['status']}<br>
                        """

                        if shelter.get("route"):
                            route = shelter["route"]
                            popup_html += f"Distance: {route['distance']['display']}<br>"
                            popup_html += f"Turns: {route['route_summary']['total_turns']}"

                        folium.Marker(
                            [slat, slon],
                            popup=folium.Popup(popup_html, max_width=300),
                            icon=folium.Icon(color=color, icon="home", prefix="fa")
                        ).add_to(m)

                        if shelter.get("route") and "path_coordinates" in shelter["route"]:
                            folium.PolyLine(
                                shelter["route"]["path_coordinates"],
                                color=color,
                                weight=4,
                                opacity=0.7,
                            ).add_to(m)

                    folium_static(m, width=1300, height=800)

                with st.expander("Technical Details"):
                    st.json(result["raw_data"])
        else:
            st.subheader("Backend response")
            st.write(result)
