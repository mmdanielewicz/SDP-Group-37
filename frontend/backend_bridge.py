import os
import sys
from typing import Dict, Any
import geocoder
from geopy.geocoders import Nominatim

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.orchestration.orchestration import main as orchestration_main
from src.response_agent.response_agent import generate_response

def guess_location():
	"""Guesses user coords using their IP address and matches it to a location name"""
	g = geocoder.ip('me')
	if not g.latlng:
		return "No location found"
	nom_agent = Nominatim(user_agent="SDP_37")
	loc = nom_agent.reverse(g.latlng, timeout=5)
	if not loc:
		return "No location address found"
	#print(loc.raw)
	address=loc.raw["address"]
	return f"{address['road']}, {address['town']}, {address['state']}"

def get_coords(name="Storrs, CT"):
	"""Returns coordinates based on place name"""
	nom_agent = Nominatim(user_agent="SDP_37")
	loc = nom_agent.geocode(name, timeout=5)
	if not loc:
		return
	return(loc.latitude,loc.longitude)

def handle_user_query(query: str, lat=None, lon=None, state="CT"):
    """
    Wrapper that calls orchestration and generates natural language response.
    
    NOTE: lat/lon parameters are currently ignored because orchestration.main()
    has hardcoded coordinates. Once orchestration is updated to accept location
    parameters, this function will pass them through.
    
    Args:
        query: User's question
        lat: Latitude (currently not used - waiting for orchestration update)
        lon: Longitude (currently not used - waiting for orchestration update)
        state: State abbreviation (defaults to CT)
    
    Returns:
        Dict with query, natural language response, and raw data
    """
    try:
        # TODO: Pass lat/lon once orchestration.main() accepts them
        # For now, orchestration uses hardcoded coordinates (41.2940, -72.3768)
        context = orchestration_main(query, lat, lon)
        
        if not context:
            return {"error": "No context returned from orchestration", "query": query}
        
        # Generate natural language response
        response_text = generate_response(query, context)
        
        # Return both for flexibility
        return {
            "query": query,
            "response": response_text,  # Human-readable
            "raw_data": context  # Still available if needed
        }
        
    except Exception as e:
        return {"error": str(e), "query": query}