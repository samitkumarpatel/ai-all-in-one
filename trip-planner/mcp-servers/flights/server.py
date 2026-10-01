"""Flights MCP server (Step 1 of the trip-planner demo).

Demonstrates: tools, resources, prompts, elicitation, progress reporting.
Run over stdio:        uv run server.py
Run over Streamable HTTP: uv run server.py http
"""
import asyncio
import sys

from fastmcp import Context, FastMCP

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
]

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
    if len(sys.argv) > 1 and sys.argv[1] == "http":
        # Streamable HTTP transport, endpoint: http://localhost:8001/mcp
        mcp.run(transport="http", host="127.0.0.1", port=8001)
    else:
        mcp.run()  # stdio