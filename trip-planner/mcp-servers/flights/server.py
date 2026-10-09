"""Flights MCP server (Steps 1 and 8 of the trip-planner demo).

Demonstrates: tools, resources, prompts, elicitation, progress reporting, and an MCP App
(a tool linked to a `ui://` HTML resource that the host renders in a sandboxed iframe).

Run over Streamable HTTP: uv run server.py        -> http://127.0.0.1:8001/mcp
Run over stdio:           uv run server.py stdio
"""
import asyncio
import os
import random
import sys
from pathlib import Path

from fastmcp import Context, FastMCP
from fastmcp.apps import AppConfig

mcp = FastMCP("flights")

# ---- Mock data -------------------------------------------------------------

AIRPORTS = {
    "CPH": "Copenhagen",
    "AMS": "Amsterdam",
    "LHR": "London Heathrow",
    "BCN": "Barcelona",
    "LIS": "Lisbon",
}

FLIGHTS = [
    {"id": "FL100", "from": "CPH", "to": "AMS", "depart": "08:15", "arrive": "09:50", "price_eur": 120},
    {"id": "FL101", "from": "CPH", "to": "AMS", "depart": "17:40", "arrive": "19:15", "price_eur": 95},
    {"id": "FL200", "from": "CPH", "to": "BCN", "depart": "06:30", "arrive": "09:35", "price_eur": 180},
    {"id": "FL300", "from": "CPH", "to": "LIS", "depart": "10:05", "arrive": "13:20", "price_eur": 210},
    {"id": "FL400", "from": "CPH", "to": "LHR", "depart": "12:00", "arrive": "13:30", "price_eur": 110},
    # Return flights
    {"id": "FL102", "from": "AMS", "to": "CPH", "depart": "10:30", "arrive": "12:00", "price_eur": 105},
    {"id": "FL103", "from": "AMS", "to": "CPH", "depart": "19:45", "arrive": "21:15", "price_eur": 130},
    {"id": "FL201", "from": "BCN", "to": "CPH", "depart": "18:10", "arrive": "21:20", "price_eur": 170},
    {"id": "FL301", "from": "LIS", "to": "CPH", "depart": "14:30", "arrive": "19:35", "price_eur": 200},
    {"id": "FL401", "from": "LHR", "to": "CPH", "depart": "16:00", "arrive": "18:55", "price_eur": 115},
]

# Seat map shape for every (mock) aircraft: rows 1..8, seats A-C | aisle | D-F
SEAT_ROWS = 8
SEAT_LETTERS = ["A", "B", "C", "D", "E", "F"]

# ---- Tools (model-controlled) ----------------------------------------------


@mcp.tool
async def search_flights(origin: str, destination: str, date: str, ctx: Context) -> list[dict]:
    """Search flights between two airport codes (e.g. CPH -> AMS) on an ISO date (YYYY-MM-DD)."""
    origin, destination = origin.upper(), destination.upper()

    # Progress reporting: fake a slow multi-provider search
    providers = ["ProviderA", "ProviderB", "ProviderC"]
    for i, name in enumerate(providers, start=1):
        await ctx.info(f"Querying {name}...")
        await asyncio.sleep(0.7)
        await ctx.report_progress(progress=i, total=len(providers))

    results = [f for f in FLIGHTS if f["from"] == origin and f["to"] == destination]
    return [{**f, "date": date} for f in results]


@mcp.tool
async def choose_seat_preference(flight_id: str, ctx: Context) -> str:
    """Ask the user for a seat preference for a flight (uses elicitation)."""
    # Elicitation: the server asks the *user* for input mid-operation
    result = await ctx.elicit(
        f"Seat preference for {flight_id}?",
        response_type=["window", "aisle", "no preference"],
    )
    if result.action == "accept":
        return f"Seat preference for {flight_id}: {result.data}"
    return f"No seat preference recorded for {flight_id} ({result.action})."


# ---- MCP App: tool + ui:// resource (Step 8) --------------------------------
#
# `app=AppConfig(resource_uri=...)` adds `_meta.ui.resourceUri` to the tool definition. A host that
# supports MCP Apps reads that resource and shows it in a sandboxed iframe next to the tool result.

SEAT_MAP_URI = "ui://flights/seat-map.html"


@mcp.tool(app=AppConfig(resource_uri=SEAT_MAP_URI))
def pick_seat(flight_id: str) -> dict:
    """Show an interactive seat map for a flight so the user can pick a seat."""
    flight_id = flight_id.upper()
    if not any(f["id"] == flight_id for f in FLIGHTS):
        raise ValueError(f"Unknown flight {flight_id}")

    # Same flight id -> same taken seats, so the demo is repeatable
    all_seats = [f"{row}{letter}" for row in range(1, SEAT_ROWS + 1) for letter in SEAT_LETTERS]
    taken = sorted(random.Random(flight_id).sample(all_seats, k=16))

    return {"flight_id": flight_id, "rows": SEAT_ROWS, "letters": SEAT_LETTERS, "taken": taken}


@mcp.resource(SEAT_MAP_URI)
def seat_map_html() -> str:
    """The seat-map MCP App (HTML). ui:// resources get the MIME type text/html;profile=mcp-app."""
    return (Path(__file__).parent / "seat_map.html").read_text()


# ---- Resources (application-controlled, read-only) -------------------------


@mcp.resource("airports://list")
def list_airports() -> dict:
    """Supported airport codes and city names."""
    return AIRPORTS


@mcp.resource("flight://{flight_id}")
def get_flight(flight_id: str) -> dict:
    """Details for a single flight by id."""
    for f in FLIGHTS:
        if f["id"] == flight_id:
            return f
    return {"error": f"Unknown flight {flight_id}"}


# ---- Prompts (user-controlled) ---------------------------------------------


@mcp.prompt(title="Plan a weekend trip")
def plan_weekend(origin: str, destination: str, date: str) -> str:
    return (
        f"Plan a weekend trip from {origin} to {destination} starting {date}. "
        "Search flights, recommend the best option by price and timing, "
        "and ask for my seat preference."
    )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        mcp.run()  # stdio: the client starts this process and talks over stdin/stdout
    else:
        # HOST=0.0.0.0 in Docker, so other containers can reach the server
        mcp.run(transport="http", host=os.getenv("HOST", "127.0.0.1"), port=8001)  # Streamable HTTP
