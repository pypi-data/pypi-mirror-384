# src/hotel_data.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

# Mock hotel database with 12+ fields
HOTELS = [
    {
        "id": "H001",
        "name": "Grand Palace Hotel",
        "description": "Luxury 5-star hotel in the heart of the city with stunning views",
        "price_per_night": 250,
        "currency": "USD",
        "location": {
            "city": "New York",
            "country": "USA",
            "address": "123 Manhattan Ave",
            "coordinates": {"lat": 40.7128, "lng": -74.0060}
        },
        "rating": 4.8,
        "total_reviews": 1234,
        "amenities": ["WiFi", "Pool", "Gym", "Spa", "Restaurant", "Bar", "Room Service"],
        "room_types": ["Single", "Double", "Suite", "Penthouse"],
        "availability": True,
        "available_rooms": 15,
        "check_in_time": "15:00",
        "check_out_time": "11:00",
        "cancellation_policy": "Free cancellation up to 24 hours before check-in",
        "contact": {
            "phone": "+1-212-555-0100",
            "email": "info@grandpalace.com",
            "website": "https://grandpalace.com"
        },
        "images": [
            "https://example.com/images/hotel1-main.jpg",
            "https://example.com/images/hotel1-room.jpg"
        ]
    },
    {
        "id": "H002",
        "name": "Beach Resort Paradise",
        "description": "Beachfront resort perfect for family vacations",
        "price_per_night": 180,
        "currency": "USD",
        "location": {
            "city": "Miami",
            "country": "USA",
            "address": "456 Ocean Drive",
            "coordinates": {"lat": 25.7617, "lng": -80.1918}
        },
        "rating": 4.5,
        "total_reviews": 856,
        "amenities": ["Beach Access", "Pool", "Kids Club", "Restaurant", "Water Sports"],
        "room_types": ["Ocean View", "Beach Front", "Family Suite"],
        "availability": True,
        "available_rooms": 8,
        "check_in_time": "14:00",
        "check_out_time": "10:00",
        "cancellation_policy": "Free cancellation up to 48 hours before check-in",
        "contact": {
            "phone": "+1-305-555-0200",
            "email": "reservations@beachparadise.com",
            "website": "https://beachparadise.com"
        },
        "images": [
            "https://example.com/images/hotel2-main.jpg",
            "https://example.com/images/hotel2-beach.jpg"
        ]
    },
    {
        "id": "H003",
        "name": "Budget Inn Downtown",
        "description": "Affordable accommodation with all basic amenities",
        "price_per_night": 75,
        "currency": "USD",
        "location": {
            "city": "Los Angeles",
            "country": "USA",
            "address": "789 Central St",
            "coordinates": {"lat": 34.0522, "lng": -118.2437}
        },
        "rating": 3.9,
        "total_reviews": 432,
        "amenities": ["WiFi", "Parking", "24hr Reception"],
        "room_types": ["Single", "Double"],
        "availability": True,
        "available_rooms": 22,
        "check_in_time": "14:00",
        "check_out_time": "11:00",
        "cancellation_policy": "Non-refundable",
        "contact": {
            "phone": "+1-213-555-0300",
            "email": "info@budgetinn.com",
            "website": "https://budgetinn.com"
        },
        "images": [
            "https://example.com/images/hotel3-main.jpg"
        ]
    }
]

# Mock bookings database
BOOKINGS = []

# Mock reviews database
REVIEWS = [
    {
        "id": "R001",
        "hotel_id": "H001",
        "guest_name": "John Doe",
        "rating": 5,
        "comment": "Absolutely amazing stay! The service was impeccable.",
        "date": "2024-10-01"
    },
    {
        "id": "R002",
        "hotel_id": "H001",
        "guest_name": "Jane Smith",
        "rating": 4,
        "comment": "Great hotel, but a bit pricey.",
        "date": "2024-09-28"
    },
    {
        "id": "R003",
        "hotel_id": "H002",
        "guest_name": "Bob Wilson",
        "rating": 5,
        "comment": "Perfect beach vacation! Kids loved it.",
        "date": "2024-10-05"
    }
]


def search_hotels(
    city: Optional[str] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    amenities: Optional[List[str]] = None,
    available_only: bool = True
) -> List[Dict]:
    """Search for hotels based on filters."""
    results = HOTELS.copy()
    
    if city:
        results = [h for h in results 
                  if city.lower() in h["location"]["city"].lower()]
    
    if max_price:
        results = [h for h in results if h["price_per_night"] <= max_price]
    
    if min_rating:
        results = [h for h in results if h["rating"] >= min_rating]
    
    if amenities:
        results = [h for h in results 
                  if all(a in h["amenities"] for a in amenities)]
    
    if available_only:
        results = [h for h in results if h["availability"]]
    
    return results


def book_hotel(
    hotel_id: str,
    guest_name: str,
    guest_email: str,
    guest_phone: str,
    check_in: str,
    check_out: str
) -> Dict:
    """Book a hotel room."""
    # Find hotel
    hotel = next((h for h in HOTELS if h["id"] == hotel_id), None)
    
    if not hotel:
        raise ValueError(f"Hotel {hotel_id} not found")
    
    if not hotel["availability"]:
        raise ValueError(f"Hotel {hotel['name']} is not available")
    
    if hotel["available_rooms"] <= 0:
        raise ValueError(f"No rooms available at {hotel['name']}")
    
    # Calculate nights
    check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
    check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
    nights = (check_out_date - check_in_date).days
    
    if nights <= 0:
        raise ValueError("Check-out must be after check-in")
    
    # Create booking
    booking = {
        "id": f"B{int(datetime.now().timestamp())}",
        "hotel_id": hotel_id,
        "hotel_name": hotel["name"],
        "guest_name": guest_name,
        "guest_email": guest_email,
        "guest_phone": guest_phone,
        "check_in": check_in,
        "check_out": check_out,
        "nights": nights,
        "total_price": hotel["price_per_night"] * nights,
        "currency": hotel["currency"],
        "status": "confirmed",
        "booking_date": datetime.now().isoformat()
    }
    
    BOOKINGS.append(booking)
    hotel["available_rooms"] -= 1
    
    return booking


def get_hotel_reviews(hotel_id: str) -> List[Dict]:
    """Get reviews for a specific hotel."""
    hotel = next((h for h in HOTELS if h["id"] == hotel_id), None)
    
    if not hotel:
        raise ValueError(f"Hotel {hotel_id} not found")
    
    reviews = [r for r in REVIEWS if r["hotel_id"] == hotel_id]
    
    return {
        "hotel_id": hotel_id,
        "hotel_name": hotel["name"],
        "total_reviews": len(reviews),
        "average_rating": sum(r["rating"] for r in reviews) / len(reviews) if reviews else 0,
        "reviews": reviews
    }