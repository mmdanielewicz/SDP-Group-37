import osmnx as ox
import networkx as nx
import geopandas as gpd
import folium
import pickle
from pyproj import Transformer


# plot the pickle file (pickle was like 3 times faster than graphml)
# G = ox.graph_from_place("Connecticut, USA", network_type="drive")
# ox.save_graphml(G, "connecticut_drive.graphml")

# # Convert GraphML to pickle (do this once to speed up loading)
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
example_json = {
    "input_location": {
        "lat": 41.807,
        "lon": -72.253
    },
    "nearest_shelters": [
        {
            "name": "University Of Connecticut Guyer Gym",
            "address": "2111 Hillside Rd",
            "city": "STORRS MANSFIELD",
            "state": "CT",
            "zip": "06269",
            "status": "CLOSED",
            "lat": 5132161.261238727,
            "lon": -8043465.968835316,
            "distance_miles": 0.19
        },
        {
            "name": "University Of Connecticut Gampel Pavilion",
            "address": "2095 HILLSIDE RD",
            "city": "STORRS MANSFIELD",
            "state": "CT",
            "zip": "06269",
            "status": "CLOSED",
            "lat": 5132225.729440598,
            "lon": -8043518.027061226,
            "distance_miles": 0.23
        },
        {
            "name": "Mansfield Community Center",
            "address": "4 South Eagleville Rd.",
            "city": "MANSFIELD",
            "state": "CT",
            "zip": "06268",
            "status": "CLOSED",
            "lat": 5131221.947840509,
            "lon": -8041858.755949676,
            "distance_miles": 0.98
        }
    ]
}

# towns = list(set(shelter["city"] for shelter in example_json["nearest_shelters"]))
# state = 'CT'


transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

shelters = {}
for s in example_json["nearest_shelters"]:
    lon, lat = transformer.transform(s["lon"], s["lat"])
    shelters[s["name"]] = [lat, lon]


# print(closest)
# print(towns)

# for t in towns:
    # place = f"{t}, {state}"
    # G = ox.graph_from_place(place, network_type='drive')
    # print(f"Loaded road network with {len(G.nodes)} nodes, {len(G.edges)} edges.")


user_lat, user_lon = example_json["input_location"]["lat"], example_json["input_location"]["lon"]
user_node = str(ox.distance.nearest_nodes(G, X=user_lon, Y=user_lat))

# print(shelters)

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
            street_name = edge_info.get('name', 'Unnamed road')
            
            # handle cases where name might be a list
            if isinstance(street_name, list):
                street_name = ', '.join(street_name)
            
            edge_names.append(street_name)
            print(f"  {u} -> {v}: {street_name}")
    
    # store edge names in routes dictionary
    routes[shelter]["edge_names"] = edge_names
    routes[shelter]["unique_streets"] = list(set(edge_names))
    
    print(f"Total edges: {len(edge_names)}")
    print(f"Unique streets: {routes[shelter]['unique_streets']}")
    # ox.plot_graph_routes(G, paths, route_linewidths=3, route_colors=ox.plot.get_colors(n=len(paths)), node_size=0)

print("\nRoute Summaries:")
for shelter, route_info in routes.items():
    miles = route_info['length'] / 1609.34
    print(f"\n{shelter}:")
    print(f"  Distance: {miles:.2f} miles ({route_info['length']:.2f} meters)")
    print(f"  Streets: {' -> '.join(route_info['unique_streets'])}")

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
    for street in route_info['edge_names']:
        if street != prev_street:  # Only show when street changes
            sidebar_html += f"<li>{street}</li>"
            prev_street = street
    
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
