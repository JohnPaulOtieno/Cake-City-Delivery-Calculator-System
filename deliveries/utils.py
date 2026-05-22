"""
Utility functions for delivery distance and fare calculations.
"""
from geopy.distance import geodesic
from django.conf import settings
import googlemaps
from decimal import Decimal
from stores.models import Store


# Pricing constants (in Kenyan Shillings)
BASE_FARE = 200  # KES for distances up to BASE_KM
BASE_KM = 10  # km
EXTRA_RATE = 50  # KES per km beyond BASE_KM


def calculate_fare(distance_km: float) -> int:
    """
    Calculate delivery fare based on distance.
    
    Pricing structure:
    - Up to 10 km: KES 200 flat rate
    - Beyond 10 km: KES 200 + (KES 50 per km)
    
    Args:
        distance_km: Distance in kilometers
        
    Returns:
        Fare amount in Kenyan Shillings (KES)
    """
    if distance_km <= 0:
        raise ValueError(f"Distance must be positive, got {distance_km}")
    
    if distance_km <= BASE_KM:
        return BASE_FARE
    
    extra_km = distance_km - BASE_KM
    total_fare = BASE_FARE + int(extra_km * EXTRA_RATE)
    
    return total_fare


def calculate_distance_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate straight-line distance between two points using Haversine formula.
    This is a fallback method when Google Maps API is unavailable.
    
    Note: This gives straight-line distance, not actual road distance.
    Actual road distances in Nairobi can be 20-40% longer.
    
    Args:
        lat1, lon1: Starting point (latitude, longitude)
        lat2, lon2: Ending point (latitude, longitude)
        
    Returns:
        Distance in kilometers
    """
    point1 = (float(lat1), float(lon1))
    point2 = (float(lat2), float(lon2))
    distance = geodesic(point1, point2)
    
    return distance.kilometers


def get_distance_from_google_maps(
    store_lat: float,
    store_lon: float,
    customer_address: str
) -> tuple:
    """
    Calculate distance from store to customer address using Google Maps Distance Matrix API.
    Returns actual road distance, not straight-line distance.
    
    Args:
        store_lat, store_lon: Store coordinates
        customer_address: Customer address string
        
    Returns:
        Tuple of (distance_km, address_decoded) or (None, None) if API fails
    """
    try:
        api_key = settings.GOOGLE_MAPS_API_KEY
        
        if not api_key or api_key == 'your-key-here':
            # Fallback to Haversine if API key not set
            return None, None
        
        gmaps = googlemaps.Client(key=api_key)
        
        # Geocode the customer address to get coordinates
        geocode_result = gmaps.geocode(customer_address)
        
        if not geocode_result:
            return None, None
        
        customer_location = geocode_result[0]['geometry']['location']
        customer_lat = customer_location['lat']
        customer_lng = customer_location['lng']
        decoded_address = geocode_result[0]['formatted_address']
        
        # Get distance from store to customer
        distance_result = gmaps.distance_matrix(
            origins=f"{store_lat},{store_lon}",
            destinations=f"{customer_lat},{customer_lng}",
            mode='driving'
        )
        
        if distance_result['rows'] and distance_result['rows'][0]['elements']:
            element = distance_result['rows'][0]['elements'][0]
            
            if element['status'] == 'OK':
                distance_meters = element['distance']['value']
                distance_km = distance_meters / 1000
                return distance_km, decoded_address, customer_lat, customer_lng
        
        return None, None, None, None
    
    except Exception as e:
        print(f"Google Maps API error: {e}")
        return None, None, None, None


def find_nearest_store(customer_lat: float, customer_lon: float) -> tuple:
    """
    Find the nearest store to a customer location using Haversine formula.
    
    Args:
        customer_lat, customer_lon: Customer coordinates
        
    Returns:
        Tuple of (store_instance, distance_km) or (None, None) if no stores found
    """
    active_stores = Store.objects.filter(is_active=True)
    
    if not active_stores.exists():
        return None, None
    
    nearest_store = None
    min_distance = float('inf')
    
    for store in active_stores:
        distance = calculate_distance_haversine(
            customer_lat, customer_lon,
            store.latitude, store.longitude
        )
        
        if distance < min_distance:
            min_distance = distance
            nearest_store = store
    
    return nearest_store, min_distance


def get_delivery_details(
    store_lat: float,
    store_lon: float,
    customer_address: str
) -> dict:
    """
    Get complete delivery details including distance and fare.
    Tries Google Maps API first, falls back to Haversine.
    
    Args:
        store_lat, store_lon: Store coordinates
        customer_address: Customer address
        
    Returns:
        Dictionary with keys:
        - distance_km: float
        - fare: int (KES)
        - decoded_address: str (verified address from geocoding)
        - customer_lat, customer_lng: float
        - method: str ('google_maps' or 'haversine')
    """
    # Try Google Maps first
    distance_data = get_distance_from_google_maps(store_lat, store_lon, customer_address)
    
    if distance_data[0] is not None:
        distance_km, decoded_address, customer_lat, customer_lng = distance_data
        return {
            'distance_km': round(float(distance_km), 2),
            'fare': calculate_fare(float(distance_km)),
            'decoded_address': decoded_address,
            'customer_lat': customer_lat,
            'customer_lng': customer_lng,
            'method': 'google_maps'
        }
    
    # Fallback to geocoding customer address manually
    try:
        gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
        geocode_result = gmaps.geocode(customer_address)
        
        if geocode_result:
            customer_location = geocode_result[0]['geometry']['location']
            customer_lat = customer_location['lat']
            customer_lng = customer_location['lng']
            decoded_address = geocode_result[0]['formatted_address']
            
            distance_km = calculate_distance_haversine(
                store_lat, store_lon, customer_lat, customer_lng
            )
            
            # Note: Haversine gives straight-line distance
            # For better accuracy, add a multiplier for road network
            road_distance = distance_km * 1.25  # Approximate road distance factor
            
            return {
                'distance_km': round(road_distance, 2),
                'fare': calculate_fare(road_distance),
                'decoded_address': decoded_address,
                'customer_lat': customer_lat,
                'customer_lng': customer_lng,
                'method': 'haversine_with_roads'
            }
    except Exception as e:
        print(f"Error in fallback geocoding: {e}")
    
    return {
        'distance_km': None,
        'fare': None,
        'decoded_address': customer_address,
        'customer_lat': None,
        'customer_lng': None,
        'method': 'error'
    }
