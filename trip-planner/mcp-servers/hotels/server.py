"""Hotels MCP server (Step 6 of the trip-planner demo).

Run over Streamable HTTP: uv run server.py        -> http://127.0.0.1:8004/mcp
Run over stdio:           uv run server.py stdio
"""
import os
import sys
from datetime import date

from fastmcp import FastMCP

mcp = FastMCP("hotels")

# ---- Mock data -------------------------------------------------------------

HOTELS = [
    {"id": "H-AMS-1", "city": "AMS", "name": "Canal House Inn", "area": "Jordaan", "stars": 4, "rating": 8.9, "price_per_night_eur": 165},
    {"id": "H-AMS-2", "city": "AMS", "name": "Budget Bike Hostel", "area": "De Pijp", "stars": 2, "rating": 7.8, "price_per_night_eur": 70},
    {"id": "H-AMS-3", "city": "AMS", "name": "Hotel Vondelpark", "area": "Museum Quarter", "stars": 5, "rating": 9.3, "price_per_night_eur": 290},
    {"id": "H-BCN-1", "city": "BCN", "name": "Gothic Quarter Suites", "area": "Barri Gotic", "stars": 4, "rating": 8.7, "price_per_night_eur": 150},
    {"id": "H-BCN-2", "city": "BCN", "name": "Beachfront Hostel", "area": "Barceloneta", "stars": 2, "rating": 7.9, "price_per_night_eur": 60},
    {"id": "H-LIS-1", "city": "LIS", "name": "Alfama View Hotel", "area": "Alfama", "stars": 4, "rating": 9.0, "price_per_night_eur": 130},
    {"id": "H-LHR-1", "city": "LHR", "name": "Kensington Rooms", "area": "Kensington", "stars": 4, "rating": 8.5, "price_per_night_eur": 220},
]

CITIES = {"AMS": "Amsterdam", "BCN": "Barcelona", "LIS": "Lisbon", "LHR": "London"}

# ---- Tools -----------------------------------------------------------------


@mcp.tool
def search_hotels(city: str, check_in: str, check_out: str) -> list[dict]:
    """Search hotels in a city (airport code, e.g. AMS) for ISO dates (YYYY-MM-DD). Sorted by price."""
    nights = (date.fromisoformat(check_out) - date.fromisoformat(check_in)).days
    if nights <= 0:
        raise ValueError("check_out must be after check_in")

    matches = [h for h in HOTELS if h["city"] == city.upper()]
    results = [
        {**h, "check_in": check_in, "check_out": check_out, "nights": nights,
         "total_eur": h["price_per_night_eur"] * nights}
        for h in matches
    ]
    return sorted(results, key=lambda h: h["total_eur"])


# ---- Resources -------------------------------------------------------------


@mcp.resource("cities://list")
def list_cities() -> dict:
    """Cities with hotel inventory (airport code -> name)."""
    return CITIES


@mcp.resource("hotel://{hotel_id}")
def get_hotel(hotel_id: str) -> dict:
    """Details for a single hotel by id."""
    for h in HOTELS:
        if h["id"] == hotel_id:
            return h
    return {"error": f"Unknown hotel {hotel_id}"}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        mcp.run()
    else:
        # HOST=0.0.0.0 in Docker, so other containers can reach the server
        mcp.run(transport="http", host=os.getenv("HOST", "127.0.0.1"), port=8004)