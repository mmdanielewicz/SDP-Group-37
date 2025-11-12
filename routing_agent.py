import osmnx as ox
import networkx as nx
import folium
from pyproj import Transformer

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

towns = list(set(shelter["city"] for shelter in example_json["nearest_shelters"]))
state = 'CT'


transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

shelters = {}
for s in example_json["nearest_shelters"]:
    lon, lat = transformer.transform(s["lon"], s["lat"])
    shelters[s["name"]] = [lat, lon]


# print(closest)
# print(towns)

for t in towns:
    place = f"{t}, {state}"
    G = ox.graph_from_place(place, network_type='drive')
    print(f"Loaded road network with {len(G.nodes)} nodes, {len(G.edges)} edges.")


    user_lat, user_lon = example_json["input_location"]["lat"], example_json["input_location"]["lon"]
    user_node = ox.distance.nearest_nodes(G, X=user_lon, Y=user_lat)

    # print(shelters)

    routes = {}
    for name, (lat, lon) in shelters.items():
        try:
            shelter_node = ox.distance.nearest_nodes(G, X=lon, Y=lat)
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
