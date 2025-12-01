import osmnx as ox
import networkx as nx
import geopandas as gpd
import folium
from pathlib import Path
import pickle
from math import atan2, degrees
import json

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


class RoutingAgent:

    _graph_cache = None
    _cache_region = None

    @staticmethod
    def get_graph_cache_path():
        """Get the path to the cache directory."""
        root_path = Path("connecticut_drive.pkl")
        if root_path.exists():
            return root_path
        
        # Otherwise use cache directory (preferred)
        cache_dir = Path(__file__).parent.parent / "cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / "connecticut_drive.pkl"
    
    @staticmethod
    def load_or_generate_graph(region="Connecticut, USA", network_type="drive", force_regenerate=False):
        """Load graph from cache or generate if it's not available. Returns a NetworkX graph."""
        cache_path = RoutingAgent.get_graph_cache_path()

        # Check if we already have it in memory
        if not force_regenerate and RoutingAgent._graph_cache is not None and RoutingAgent._cache_region == region:
            print(f"Using cached graph from memory for {region}")
            return RoutingAgent._graph_cache
        
        # Check if we have it on disk
        if not force_regenerate and cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    G = pickle.load(f)
                RoutingAgent._graph_cache = G
                RoutingAgent._cache_region = region
                return G
            except Exception as e:
                print(f"Error loading cached graph: {e}.")
        
        # Generate new graph if not cached
        print(f"Generating new graph for {region}. Will take a few minutes.")
        try:
            G = ox.graph_from_place(region, network_type=network_type)
            
            # Save to cache
            with open(cache_path, 'wb') as f:
                pickle.dump(G, f)
            
            # Store in memory
            RoutingAgent._graph_cache = G
            RoutingAgent._cache_region = region
            
            return G
        except Exception as e:
            raise RuntimeError(f"Failed to generate graph: {e}")



    @staticmethod
    def compute_bearing(lat1, lon1, lat2, lon2):
        '''Helper function to compute bearing between two lat/lon points for directions'''
        angle = atan2((lon2 - lon1), (lat2 - lat1))
        bearing = degrees(angle)
        return (bearing + 360) % 360

    @staticmethod
    def turn_direction(b1, b2):
        '''Helper function to determine turn direction based on bearings'''
        diff = (b2 - b1 + 360) % 360
        if diff < 30 or diff > 330:
            return "Continue straight"
        elif diff < 180:
            return "Turn right"
        else:
            return "Turn left"

    @staticmethod
    def get_street_name(edge_info):
        '''Extract street names from edge information.'''

        highway_label_map = {
            "motorway": "Highway",
            "motorway_link": "Highway Ramp",
            "trunk": "State Route",
            "trunk_link": "State Route Ramp",
            "primary": "Main Road",
            "secondary": "Secondary Road"
        }

        name = edge_info.get("name")

        # If it's a list, join it
        if isinstance(name, list):
            name = ", ".join(name)

        # If no name, try the "ref" like I-95 or US-1
        if not name:
            name = edge_info.get("ref")

        # Check major roads
        if not name:
            hw = edge_info.get("highway")
            if isinstance(hw, list):
                hw = hw[0]
            if hw:
                # Format better
                label = highway_label_map.get(hw, hw.title())
                name = label

        if not name:
            name = "Unnamed Road"

        return name


    @staticmethod
    def format_directions_narrative(directions):
        """Convert directions list into natural language response."""
        if not directions:
            return ""
        
        narrative_parts = []
        for i, direction in enumerate(directions, 1):
            if i == len(directions): 
                narrative_parts.append(direction)
            else:
                narrative_parts.append(f"{i}. {direction}")
        
        return "\n".join(narrative_parts)


    @staticmethod
    def get_routes(user_lat, user_lon, shelters, max_results=5):
        '''Main computation to get routes from user location to shelters.'''

        # with open('connecticut_drive.pkl', 'rb') as f:
        #     G = pickle.load(f)

        # Try to load graph
        try:
            G = RoutingAgent.load_or_generate_graph()
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load routing data: {e}",
                "user_location": {"lat": user_lat, "lon": user_lon},
                "routes": []
            }


        # User location setup
        try:
            user_node = (ox.distance.nearest_nodes(G, X=user_lon, Y=user_lat))
        except Exception as e:
            return {
                "success": False,
                "error": f"Could not locate user position: {e}",
                "user_location": {"lat": user_lat, "lon": user_lon},
                "routes": []
            }


        # compute routes
        routes = {}
        for name, coords in shelters.items():
            lat, lon = coords[0], coords[1]
            try:
                shelter_node = (ox.distance.nearest_nodes(G, X=lon, Y=lat))
                path = nx.shortest_path(G, user_node, shelter_node, weight="length")
                length = nx.shortest_path_length(G, user_node, shelter_node, weight="length")
                routes[name] = {
                    "path": path,
                    "length": length,
                    "shelter_lat": lat,
                    "shelter_lon": lon
                }
            except nx.NetworkXNoPath:
                print(f"No route found to {name}")
                continue
            except Exception as e:
                print(f"Error computing route to {name}: {e}")
                continue

        # paths = [info["path"] for _, info in routes.items()]

        for shelter, route_info in routes.items():
            path = route_info["path"]
            edge_names = []
            directions = []
            prev_bearing = None
            prev_street = None

            # print(f"\nRoute to {shelter}:")

            for i in range(len(path) - 1):
                u = path[i]  
                v = path[i + 1] 
                

                # may show multiple edges bc of MultiDiGraph
                edge_data = G.get_edge_data(u, v)
                
                if edge_data:
                    # if multiple edges exist, get the first one
                    edge_info = edge_data.get(0, edge_data) if isinstance(edge_data, dict) else edge_data
                    street_name = RoutingAgent.get_street_name(edge_info)

                    # If it's a list, join
                    if isinstance(street_name, list):
                        street_name = ", ".join(street_name)
                    
                    edge_names.append(street_name)
                    # print(f"  {u} -> {v}: {street_name}")

                    lat1, lon1 = G.nodes[u]['y'], G.nodes[u]['x']
                    lat2, lon2 = G.nodes[v]['y'], G.nodes[v]['x']
                    bearing = RoutingAgent.compute_bearing(lat1, lon1, lat2, lon2)

                    # First instruction
                    if prev_bearing is None:
                        directions.append(f"Start on {street_name}")
                    else:
                        if street_name != prev_street:
                            maneuver = RoutingAgent.turn_direction(prev_bearing, bearing)
                            directions.append(f"{maneuver} onto {street_name}")

                    prev_bearing = bearing
                    prev_street = street_name

                
            
            # store edge names in routes dictionary
            routes[shelter]["edge_names"] = edge_names
            routes[shelter]["unique_streets"] = list(set(edge_names))
            routes[shelter]["directions"] = directions


        route_list = []
        for shelter_name, route_info in routes.items():
            distance_miles = route_info["length"] / 1609.34
            
            route_list.append({
                "shelter_name": shelter_name,
                "location": {
                    "lat": route_info["shelter_lat"],
                    "lon": route_info["shelter_lon"]
                },
                "distance": {
                    "meters": round(route_info["length"], 1),
                    "miles": round(distance_miles, 2),
                    "display": f"{distance_miles:.1f} miles"
                },
                "route_summary": {
                    "major_roads": route_info["unique_streets"][:5], 
                    "total_turns": len(route_info["directions"]) - 2,  
                },
                "directions": {
                    "steps": route_info["directions"],
                    "narrative": RoutingAgent.format_directions_narrative(route_info["directions"])
                }
            })

        # Sort by distance
        route_list.sort(key=lambda x: x["distance"]["meters"])
        
        # Limit results
        limited_routes = route_list[:max_results]

        # Create final structured response
        result = {
            "success": True,
            "user_location": {
                "lat": user_lat,
                "lon": user_lon
            },
            "summary": {
                "total_shelters_found": len(limited_routes),
                "nearest_shelter": limited_routes[0]["shelter_name"] if limited_routes else None,
                "nearest_distance": limited_routes[0]["distance"]["display"] if limited_routes else None,
            },
            "routes": limited_routes,
            # LLM-friendly summary for quick parsing
            "llm_context": {
                "quick_summary": f"Found {len(shelters)} shelters within range. The closest is {limited_routes[0]['shelter_name']} at {limited_routes[0]['distance']['display']} )." if limited_routes else "No shelters found.",
                "top_3_options": [
                    {
                        "name": route["shelter_name"],
                        "distance": route["distance"]["display"],
                        "first_direction": route["directions"]["steps"][0] if route["directions"]["steps"] else ""
                    }
                    for route in limited_routes[:3]
                ]
            }
        }

        return result




