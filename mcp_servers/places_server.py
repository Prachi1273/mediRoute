"""
Places API — MCP Server
-----------------------
Wraps Google Maps Places API to find nearby healthcare facilities.
Requires GOOGLE_MAPS_API_KEY environment variable.

Day 2 course concept: MCP server connecting to an external API.
Security: API key is read from env — never hardcoded (Day 4).
"""

import os
import json
import urllib.request
import urllib.parse
from mcp.server import MCPServer

MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
PLACES_BASE = "https://maps.googleapis.com/maps/api/place"

app = MCPServer(name="places_api", version="1.0.0")

# Mapping from urgency level to Google Places types to search
URGENCY_TO_PLACE_TYPE = {
    "EMERGENCY": ["hospital"],
    "URGENT": ["hospital", "doctor"],
    "ROUTINE": ["doctor", "pharmacy"],
}


def _call_places_api(endpoint: str, params: dict) -> dict:
    """Make a GET request to the Google Places API."""
    if not MAPS_API_KEY:
        # Return mock data for local dev / demo without a real key
        return _mock_places_response(params)

    params["key"] = MAPS_API_KEY
    url = f"{PLACES_BASE}/{endpoint}/json?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read())


def _mock_places_response(params: dict) -> dict:
    """Return realistic mock data when no API key is set."""
    return {
        "status": "OK",
        "results": [
            {
                "name": "Ruby Hall Clinic",
                "vicinity": "40 Sassoon Road, Pune",
                "geometry": {"location": {"lat": 18.5195, "lng": 73.8553}},
                "opening_hours": {"open_now": True},
                "formatted_phone_number": "+91-20-66455000",
                "place_id": "mock_place_1",
            },
            {
                "name": "KEM Hospital",
                "vicinity": "489 Rasta Peth, Pune",
                "geometry": {"location": {"lat": 18.5159, "lng": 73.8567}},
                "opening_hours": {"open_now": True},
                "formatted_phone_number": "+91-20-26128000",
                "place_id": "mock_place_2",
            },
            {
                "name": "Jehangir Hospital",
                "vicinity": "32 Sassoon Road, Pune",
                "geometry": {"location": {"lat": 18.5211, "lng": 73.8549}},
                "opening_hours": {"open_now": True},
                "formatted_phone_number": "+91-20-66810000",
                "place_id": "mock_place_3",
            },
        ],
    }


def _haversine_km(lat1, lng1, lat2, lng2) -> float:
    """Calculate straight-line distance between two GPS points in km."""
    import math
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


@app.tool(
    name="search_nearby",
    description="Find healthcare facilities near a GPS location filtered by urgency level.",
    input_schema={
        "type": "object",
        "properties": {
            "lat": {"type": "number"},
            "lng": {"type": "number"},
            "urgency": {"type": "string", "enum": ["EMERGENCY", "URGENT", "ROUTINE"]},
            "radius_m": {"type": "integer", "default": 5000},
        },
        "required": ["lat", "lng", "urgency"],
    },
)
def search_nearby(lat: float, lng: float, urgency: str, radius_m: int = 5000) -> dict:
    """Search for nearby healthcare facilities."""
    place_types = URGENCY_TO_PLACE_TYPE.get(urgency, ["doctor"])
    all_results = []

    for place_type in place_types:
        data = _call_places_api("nearbysearch", {
            "location": f"{lat},{lng}",
            "radius": radius_m,
            "type": place_type,
            "keyword": "hospital clinic health",
        })
        all_results.extend(data.get("results", []))

    # Deduplicate, compute distances, sort
    seen = set()
    facilities = []
    for place in all_results:
        pid = place.get("place_id", place["name"])
        if pid in seen:
            continue
        seen.add(pid)
        plat = place["geometry"]["location"]["lat"]
        plng = place["geometry"]["location"]["lng"]
        dist = _haversine_km(lat, lng, plat, plng)
        facilities.append({
            "name": place["name"],
            "address": place.get("vicinity", ""),
            "distance_km": round(dist, 2),
            "open_now": place.get("opening_hours", {}).get("open_now", None),
            "phone": place.get("formatted_phone_number", ""),
            "maps_url": f"https://maps.google.com/?q={urllib.parse.quote(place['name'])}",
            "place_id": pid,
        })

    facilities.sort(key=lambda x: x["distance_km"])
    return {"facilities": facilities[:3], "urgency": urgency}


@app.tool(
    name="get_place_details",
    description="Get full details (hours, phone, rating) for a specific place ID.",
    input_schema={
        "type": "object",
        "properties": {
            "place_id": {"type": "string"},
        },
        "required": ["place_id"],
    },
)
def get_place_details(place_id: str) -> dict:
    """Fetch detailed info for a place."""
    data = _call_places_api("details", {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,opening_hours,rating,website",
    })
    return data.get("result", {})


@app.tool(
    name="get_directions",
    description="Get Google Maps directions URL from user location to a facility.",
    input_schema={
        "type": "object",
        "properties": {
            "from_lat": {"type": "number"},
            "from_lng": {"type": "number"},
            "to_place_id": {"type": "string"},
        },
        "required": ["from_lat", "from_lng", "to_place_id"],
    },
)
def get_directions(from_lat: float, from_lng: float, to_place_id: str) -> dict:
    """Return a Google Maps directions URL."""
    url = (
        f"https://www.google.com/maps/dir/?api=1"
        f"&origin={from_lat},{from_lng}"
        f"&destination_place_id={to_place_id}"
        f"&travelmode=driving"
    )
    return {"directions_url": url}


if __name__ == "__main__":
    app.run(transport="stdio")
