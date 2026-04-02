"""Mock Flight Booking API — returns fake data for development."""

import os
import random
import secrets
import string
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

app = FastAPI(title="Mock Flight Booking API")
security = HTTPBasic()

API_USERNAME = os.getenv("FLIGHT_API_USERNAME", "admin")
API_PASSWORD = os.getenv("FLIGHT_API_PASSWORD", "changeme")
CARD_ENCRYPTION_KEY = os.getenv("CARD_ENCRYPTION_KEY", "")

if not CARD_ENCRYPTION_KEY:
    CARD_ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"WARNING: No CARD_ENCRYPTION_KEY set. Generated ephemeral key: {CARD_ENCRYPTION_KEY}")

fernet = Fernet(CARD_ENCRYPTION_KEY.encode() if isinstance(CARD_ENCRYPTION_KEY, str) else CARD_ENCRYPTION_KEY)


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username, API_USERNAME)
    correct_pass = secrets.compare_digest(credentials.password, API_PASSWORD)
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def _confirmation_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


class SearchRequest(BaseModel):
    departure_airport: str
    arrival_airport: str
    departure_date: str
    return_date: str = ""


class BookRequest(BaseModel):
    flight_id: str
    passenger_name: str


class PaymentRequest(BaseModel):
    flight_id: str
    card_type: str
    encrypted_card_number: str
    expiration_date: str
    amount: float

    @field_validator("amount", mode="before")
    @classmethod
    def coerce_amount(cls, v):
        return float(v)


@app.post("/search_flights")
def search_flights(req: SearchRequest, _user: str = Depends(verify_credentials)):
    dep = req.departure_airport.upper()
    arr = req.arrival_airport.upper()
    flights = [
        {
            "flight_id": "FL1001",
            "airline": "Delta Airlines",
            "departure_airport": dep,
            "arrival_airport": arr,
            "departure_date": req.departure_date,
            "departure_time": "08:30",
            "arrival_time": "11:45",
            "price_usd": 320,
            "class": "economy",
        },
        {
            "flight_id": "FL1002",
            "airline": "Delta Airline",
            "departure_airport": dep,
            "arrival_airport": arr,
            "departure_date": req.departure_date,
            "departure_time": "14:15",
            "arrival_time": "17:30",
            "price_usd": 275,
            "class": "economy",
        },
    ]
    if req.return_date:
        flights.append(
            {
                "flight_id": "FL2001",
                "airline": "Delta Airlines",
                "departure_airport": arr,
                "arrival_airport": dep,
                "departure_date": req.return_date,
                "departure_time": "10:00",
                "arrival_time": "13:15",
                "price_usd": 310,
                "class": "economy",
            }
        )
    return {"flights": flights}


@app.post("/book_flight")
def book_flight(req: BookRequest, _user: str = Depends(verify_credentials)):
    return {
        "status": "confirmed",
        "confirmation_code": _confirmation_code(),
        "flight_id": req.flight_id,
        "passenger_name": req.passenger_name,
        "message": f"Flight {req.flight_id} booked successfully for {req.passenger_name}.",
    }


@app.post("/process_payment")
def process_payment(req: PaymentRequest, _user: str = Depends(verify_credentials)):
    try:
        card_number = fernet.decrypt(req.encrypted_card_number.encode()).decode()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or corrupted card data.")
    last_four = card_number[-4:]
    return {
        "status": "success",
        "transaction_id": "TXN" + _confirmation_code(),
        "flight_id": req.flight_id,
        "card_type": req.card_type,
        "card_last_four": last_four,
        "expiration_date": req.expiration_date,
        "amount_charged": req.amount,
        "message": f"Payment of ${req.amount:.2f} processed successfully via {req.card_type} ending in {last_four}.",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
