import osmnx as ox
import networkx as nx
import geopandas as gpd
import folium
import pickle
from math import atan2, degrees

# # plot the pickle file (pickle was like 3 times faster than graphml)
# G = ox.graph_from_place("Connecticut, USA", network_type="drive")
# ox.save_graphml(G, "connecticut_drive.graphml")

# # Convert GraphML to pickle
# G = nx.read_graphml("connecticut_drive.graphml")
# for node in G.nodes():
#     G.nodes[node]['x'] = float(G.nodes[node]['x'])
#     G.nodes[node]['y'] = float(G.nodes[node]['y'])
# for u, v, key, data in G.edges(keys=True, data=True):
#     if 'length' in data:
#         G[u][v][key]['length'] = float(data['length'])
# with open('connecticut_drive.pkl', 'wb') as f:
#     pickle.dump(G, f)
# print("Saved pickle file")

with open('connecticut_drive.pkl', 'rb') as f:
    G = pickle.load(f)
 

# example json from data agent for building and testing
# example_json = {
#     "input_location": {
#         "lat": 41.807,
#         "lon": -72.253
#     },
#     "nearest_shelters": [
#         {
#             "name": "University Of Connecticut Guyer Gym",
#             "address": "2111 Hillside Rd",
#             "city": "STORRS MANSFIELD",
#             "state": "CT",
#             "zip": "06269",
#             "status": "CLOSED",
#             "lat": 5132161.261238727,
#             "lon": -8043465.968835316,
#             "distance_miles": 0.19
#         },
#         {
#             "name": "University Of Connecticut Gampel Pavilion",
#             "address": "2095 HILLSIDE RD",
#             "city": "STORRS MANSFIELD",
#             "state": "CT",
#             "zip": "06269",
#             "status": "CLOSED",
#             "lat": 5132225.729440598,
#             "lon": -8043518.027061226,
#             "distance_miles": 0.23
#         },
#         {
#             "name": "Mansfield Community Center",
#             "address": "4 South Eagleville Rd.",
#             "city": "MANSFIELD",
#             "state": "CT",
#             "zip": "06268",
#             "status": "CLOSED",
#             "lat": 5131221.947840509,
#             "lon": -8041858.755949676,
#             "distance_miles": 0.98
#         }
#     ]
# }

example_json = {
  "input_location": {
    "lat": 41.293774,
    "lon": -72.378348
  },
  "nearest_shelters": [
    {
      "name": "Old Saybrook High School",
      "address": "1111 BOSTON POST RD",
      "city": "OLD SAYBROOK",
      "state": "CT",
      "zip": "06475",
      "status": "CLOSED",
      "lat": 41.28841649000003,
      "lon": -72.38944033599995,
      "distance_miles": 0.69,
      "handicap_accessible": "No",
    },
    {
      "name": "Old Lyme Center School",
      "address": "49 Lyme Street",
      "city": "OLD LYME",
      "state": "CT",
      "zip": "06371",
      "status": "CLOSED",
      "lat": 41.31681707900003,
      "lon": -72.32970736699997,
      "distance_miles": 2.99,
      "handicap_accessible": "No",
    },
    {
      "name": "Old Lyme Town Hall",
      "address": "52 Lyme Street",
      "city": "OLD LYME",
      "state": "CT",
      "zip": "06371",
      "status": "CLOSED",
      "lat": 41.316871038000045,
      "lon": -72.32970736699997,
      "distance_miles": 2.99,
      "handicap_accessible": "Yes",
    },
  ]
}

# towns = list(set(shelter["city"] for shelter in example_json["nearest_shelters"]))
# state = 'CT'

shelters = {}
for s in example_json["nearest_shelters"]:
    lon, lat = (s["lon"], s["lat"])
    shelters[s["name"]] = [lat, lon]

# User location setup
user_lat, user_lon = example_json["input_location"]["lat"], example_json["input_location"]["lon"]
user_node = str(ox.distance.nearest_nodes(G, X=user_lon, Y=user_lat))

# functions for computing actual directions based on edge angles
def compute_bearing(lat1, lon1, lat2, lon2):
    angle = atan2((lon2 - lon1), (lat2 - lat1))
    bearing = degrees(angle)
    return (bearing + 360) % 360

def turn_direction(b1, b2):
    diff = (b2 - b1 + 360) % 360
    if diff < 30 or diff > 330:
        return "Continue straight"
    elif diff < 180:
        return "Turn right"
    else:
        return "Turn left"


# compute routes
routes = {}
for name, (lat, lon) in shelters.items():
    try:
        shelter_node = str(ox.distance.nearest_nodes(G, X=lon, Y=lat))
        path = nx.shortest_path(G, user_node, shelter_node, weight="length")
        length = nx.shortest_path_length(G, user_node, shelter_node, weight="length")
        routes[name] = {"path": path, "length": length}
    except nx.NetworkXNoPath:
        continue

# paths = [info["path"] for _, info in routes.items()]

for shelter, route_info in routes.items():
    path = route_info["path"]
    edge_names = []
    directions = []
    prev_bearing = None
    prev_street = None

    print(f"\nRoute to {shelter}:")

    for i in range(len(path) - 1):
        u = path[i]  
        v = path[i + 1] 
        

        # may show multiple edges bc of MultiDiGraph
        edge_data = G.get_edge_data(u, v)
        
        if edge_data:
            # if multiple edges exist, get the first one
            edge_info = edge_data.get(0, edge_data) if isinstance(edge_data, dict) else edge_data
            
            # get the street name
            street_name = edge_info.get("name")
            if not street_name:
                street_name = edge_info.get("ref", "Unnamed road")

            # If it's a list, join
            if isinstance(street_name, list):
                street_name = ", ".join(street_name)
            
            edge_names.append(street_name)
            print(f"  {u} -> {v}: {street_name}")

            lat1, lon1 = G.nodes[u]['y'], G.nodes[u]['x']
            lat2, lon2 = G.nodes[v]['y'], G.nodes[v]['x']
            bearing = compute_bearing(lat1, lon1, lat2, lon2)

            # First instruction
            if prev_bearing is None:
                directions.append(f"Start on {street_name}")
            else:
                if street_name != prev_street:
                    maneuver = turn_direction(prev_bearing, bearing)
                    directions.append(f"{maneuver} onto {street_name}")

            prev_bearing = bearing
            prev_street = street_name

        
    
    # store edge names in routes dictionary
    routes[shelter]["edge_names"] = edge_names
    routes[shelter]["unique_streets"] = list(set(edge_names))
    routes[shelter]["directions"] = directions
    directions.append(f"Arrive at {name}")
    
    # print(f"Total edges: {len(edge_names)}")
    # print(f"Unique streets: {routes[shelter]['unique_streets']}")
    # ox.plot_graph_routes(G, paths, route_linewidths=3, route_colors=ox.plot.get_colors(n=len(paths)), node_size=0)

print("\nRoute Summaries:")
for shelter, route_info in routes.items():
    miles = route_info['length'] / 1609.34
    print(f"\n{shelter}:")
    print(f"  Distance: {miles:.2f} miles ({route_info['length']:.2f} meters)")
    print(f"  Streets: {' -> '.join(route_info['unique_streets'])}")
    for step in route_info["directions"]:
        print("   -", step)

    # print(paths)

# static plot of routes

# print(paths)

    

# create map centered on user location
m = folium.Map(location=[user_lat, user_lon], zoom_start=14)

sidebar_html = """
<div style="position: fixed; 
            top: 10px; 
            right: 10px; 
            width: 350px; 
            height: 90vh; 
            background-color: white; 
            border: 2px solid black; 
            border-radius: 5px;
            z-index: 9999; 
            padding: 15px;">
    <h3 style="margin-top: 0; margin-bottom: 15px; color: #333;">Shelter Routes</h3>
"""

for name, route_info in routes.items():
    miles = route_info['length'] / 1609.34
    sidebar_html += f"""
    <div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #ddd;">
        <h4 style="color: red; margin-bottom: 5px;">{name}</h4>
        <p style="margin: 5px 0; font-size: 14px;"><strong>Distance:</strong> {miles:.2f} miles</p>
        <p style="margin: 5px 0; font-size: 12px;"><strong>Directions:</strong></p>
        <ol style="margin: 5px 0; padding-left: 20px; font-size: 12px;">
"""
    
    # Add turn-by-turn directions
    prev_street = None
    for step in route_info['directions']:
        sidebar_html += f"<li>{step}</li>"

    
    sidebar_html += """
        </ol>
    </div>
"""

sidebar_html += "</div>"

m.get_root().html.add_child(folium.Element(sidebar_html))

# add marker for user location
folium.Marker(
    [user_lat, user_lon],
    popup="User Location",
    icon=folium.Icon(color="blue", icon="user")
).add_to(m)

# add markers for shelters
for name, (lat, lon) in shelters.items():
    folium.Marker(
        [lat, lon],
        popup=name,
        icon=folium.Icon(color="red", icon="home")
    ).add_to(m)

# plot the route lines
for name, route in routes.items():
    nodes = route["path"]
    lines = []
    for i in range(len(nodes) - 1):
        pt1 = (G.nodes[nodes[i]]['y'], G.nodes[nodes[i]]['x'])
        pt2 = (G.nodes[nodes[i+1]]['y'], G.nodes[nodes[i+1]]['x'])
        lines.append([pt1, pt2])

    folium.PolyLine(
        [p for seg in lines for p in seg],
        color="green",
        weight=3,
        popup=f"Route to {name}"
    ).add_to(m)

m.save("routes_map.html")
print("Saved map to routes_map.html")
