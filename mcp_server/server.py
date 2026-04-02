"""MCP server that wraps the Mock Flight Booking API."""

import json
import os
import httpx
import pybreaker
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

API_BASE = "http://localhost:8001"
API_USERNAME = os.getenv("FLIGHT_API_USERNAME", "admin")
API_PASSWORD = os.getenv("FLIGHT_API_PASSWORD", "changeme")
API_AUTH = (API_USERNAME, API_PASSWORD)

flight_api_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=30,
    name="flight-api",
)

mcp = FastMCP("flight-booking")


@mcp.tool()
def search_flights(
    departure_airport: str,
    arrival_airport: str,
    departure_date: str,
    return_date: str = "",
) -> str:
    """Search available flights between two airports.

    Args:
        departure_airport: IATA code of the departure airport (e.g. JFK).
        arrival_airport: IATA code of the arrival airport (e.g. LAX).
        departure_date: Departure date in YYYY-MM-DD format.
        return_date: Optional return date in YYYY-MM-DD format for round trips.
    """
    try:
        resp = flight_api_breaker.call(
            httpx.post,
            f"{API_BASE}/search_flights",
            auth=API_AUTH,
            json={
                "departure_airport": departure_airport,
                "arrival_airport": arrival_airport,
                "departure_date": departure_date,
                "return_date": return_date,
            },
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)
    except pybreaker.CircuitBreakerError:
        return json.dumps({"error": "Flight API is temporarily unavailable. Please try again later."})


@mcp.tool()
def book_flight(flight_id: str, passenger_name: str) -> str:
    """Book a specific flight for a passenger. This only creates a reservation.
    Payment must be processed separately using process_payment after booking.

    Args:
        flight_id: The flight ID returned by search_flights (e.g. FL1001).
        passenger_name: Full name of the passenger.
    """
    try:
        resp = flight_api_breaker.call(
            httpx.post,
            f"{API_BASE}/book_flight",
            auth=API_AUTH,
            json={"flight_id": flight_id, "passenger_name": passenger_name},
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)
    except pybreaker.CircuitBreakerError:
        return json.dumps({"error": "Flight API is temporarily unavailable. Please try again later."})


@mcp.tool()
def process_payment(
    flight_id: str,
    card_type: str,
    encrypted_card_number: str,
    expiration_date: str,
    amount: str,
) -> str:
    """Process payment for a booked flight. Must be called after book_flight to complete the booking.

    Args:
        flight_id: The flight ID to pay for (e.g. FL1001).
        card_type: Payment card type — one of 'visa', 'mastercard', or 'amex'.
        encrypted_card_number: The encrypted card number token (do NOT pass raw card numbers).
        expiration_date: Card expiration date in MM/YYYY format.
        amount: The amount to charge in USD (e.g. '320' or '320.00').
    """
    try:
        parsed_amount = float(amount)
    except (ValueError, TypeError):
        return json.dumps({"error": f"Invalid amount: {amount}"})
    try:
        resp = flight_api_breaker.call(
            httpx.post,
            f"{API_BASE}/process_payment",
            auth=API_AUTH,
            json={
                "flight_id": flight_id,
                "card_type": card_type,
                "encrypted_card_number": encrypted_card_number,
                "expiration_date": expiration_date,
                "amount": parsed_amount,
            },
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)
    except pybreaker.CircuitBreakerError:
        return json.dumps({"error": "Payment API is temporarily unavailable. Please try again later."})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"Payment failed: {e.response.json().get('detail', str(e))}"})


if __name__ == "__main__":
    mcp.run(transport="stdio")
