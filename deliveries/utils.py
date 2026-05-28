"""
Utility functions for delivery distance and fare calculations.

Primary:  Google Maps Distance Matrix API (real road distance).
Fallback: OpenStreetMap Nominatim + Haversine (when API key is missing/invalid).
"""
import requests
import googlemaps
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from django.conf import settings
from stores.models import Store


from deliveries.models import PricingConfiguration

def calculate_fare(distance_km: float) -> int:
    """
    Calculate delivery fare based on distance using the PricingConfiguration in the database.

    Pricing (default):
      ≤ 10 km → KES 200 flat rate
      > 10 km → KES 200 + (KES 50 × extra km)

    Args:
        distance_km: Distance in kilometres (must be > 0)

    Returns:
        Fare in Kenyan Shillings
    """
    if distance_km <= 0:
        raise ValueError(f"Distance must be positive, got {distance_km}")

    try:
        config = PricingConfiguration.get_settings()
        base_fare = config.base_fare
        base_km = float(config.base_km)
        extra_rate = config.extra_rate_per_km
    except Exception as e:
        # Fallback if DB isn't ready
        base_fare = 200
        base_km = 10.0
        extra_rate = 50
        print(f"[pricing] Fallback pricing used: {e}")

    if distance_km <= base_km:
        return base_fare

    return base_fare + int((distance_km - base_km) * extra_rate)


# ── Haversine (straight-line) distance ────────────────────────────────────────

def calculate_distance_haversine(lat1: float, lon1: float,
                                 lat2: float, lon2: float) -> float:
    """Straight-line distance in km via Haversine formula."""
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers


# ── Google Maps helpers ───────────────────────────────────────────────────────

def _gmaps_client():
    """Return a googlemaps.Client if a valid key is configured, else None."""
    key = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
    if not key or key in ("your-key-here", "your-google-maps-api-key-here"):
        return None
    try:
        return googlemaps.Client(key=key)
    except Exception as exc:
        print(f"[maps] Could not create Google Maps client: {exc}")
        return None


def geocode_with_google(address: str) -> dict | None:
    """
    Geocode an address using the Google Geocoding API.

    Returns dict with keys lat, lng, display_name  — or None on failure.
    """
    client = _gmaps_client()
    if not client:
        return None
    try:
        results = client.geocode(address, region="ke",
                                 bounds={"southwest": (-1.444, 36.650),
                                         "northeast": (-1.150, 37.103)})
        if results:
            loc = results[0]["geometry"]["location"]
            return {
                "lat": loc["lat"],
                "lng": loc["lng"],
                "display_name": results[0]["formatted_address"],
            }
    except Exception as exc:
        print(f"[maps] Geocoding error: {exc}")
    return None


def get_road_distance_google(store_lat: float, store_lng: float,
                              cust_lat: float, cust_lng: float) -> float | None:
    """
    Real driving distance (km) via Google Distance Matrix API.

    Returns distance in km, or None on failure.
    """
    client = _gmaps_client()
    if not client:
        return None
    try:
        result = client.distance_matrix(
            origins=f"{store_lat},{store_lng}",
            destinations=f"{cust_lat},{cust_lng}",
            mode="driving",
        )
        rows = result.get("rows", [])
        if rows and rows[0].get("elements"):
            element = rows[0]["elements"][0]
            if element.get("status") == "OK":
                return element["distance"]["value"] / 1000   # metres → km
    except Exception as exc:
        print(f"[maps] Distance Matrix error: {exc}")
    return None


# ── Nominatim fallback geocoding ──────────────────────────────────────────────

def geocode_with_nominatim(address: str) -> dict | None:
    """
    Geocode via OpenStreetMap Nominatim (free, no key needed).
    Biased to Nairobi, Kenya.
    """
    try:
        query = address
        if "nairobi" not in address.lower() and "kenya" not in address.lower():
            query = f"{address}, Nairobi, Kenya"

        geolocator = Nominatim(user_agent="cake_delivery_nairobi/1.0")
        location = geolocator.geocode(
            query,
            timeout=10,
            exactly_one=True,
            viewbox=[(36.650, -1.444), (37.103, -1.150)],
            bounded=True,
        )
        if location:
            return {
                "lat": location.latitude,
                "lng": location.longitude,
                "display_name": location.address,
            }
        # Retry without bounding box
        location = geolocator.geocode(query, timeout=10, exactly_one=True)
        if location:
            return {
                "lat": location.latitude,
                "lng": location.longitude,
                "display_name": location.address,
            }
    except (GeocoderTimedOut, GeocoderServiceError) as exc:
        print(f"[nominatim] Geocoding error: {exc}")
    except Exception as exc:
        print(f"[nominatim] Unexpected error: {exc}")
    return None


# ── Address autocomplete (used by the /api/address-autocomplete/ endpoint) ────

def search_address_suggestions(query: str, limit: int = 7) -> list:
    """
    Return address autocomplete suggestions biased to Nairobi.
    Uses Google Places Autocomplete API if available; falls back to Nominatim.
    """
    if not query or len(query.strip()) < 3:
        return []

    client = _gmaps_client()
    if client:
        return _suggestions_google(client, query, limit)
    return _suggestions_nominatim(query, limit)


def _suggestions_google(client, query: str, limit: int) -> list:
    """Google Places Autocomplete suggestions."""
    try:
        response = client.places_autocomplete(
            input_text=query,
            location=(-1.286389, 36.817223),   # Nairobi centre
            radius=50_000,                      # 50 km bias radius
            components={"country": "ke"},
        )
        suggestions = []
        for item in response[:limit]:
            desc = item.get("description", "")
            place_id = item.get("place_id", "")

            # Resolve place_id → lat/lng
            lat, lng = None, None
            try:
                detail = client.place(
                    place_id,
                    fields=["geometry"],
                )
                geo = detail.get("result", {}).get("geometry", {}).get("location", {})
                lat = geo.get("lat")
                lng = geo.get("lng")
            except Exception:
                pass   # coords optional — fare preview will geocode if missing

            suggestions.append({
                "display_name": desc,
                "lat": lat,
                "lng": lng,
                "place_id": place_id,
            })
        return suggestions
    except Exception as exc:
        print(f"[maps] Places Autocomplete error: {exc}")
        return _suggestions_nominatim(query, limit)


def _suggestions_nominatim(query: str, limit: int) -> list:
    """Nominatim search suggestions (fallback)."""
    search_q = query.strip()
    if "nairobi" not in search_q.lower() and "kenya" not in search_q.lower():
        search_q = f"{search_q}, Nairobi, Kenya"

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": search_q,
        "format": "json",
        "limit": limit,
        "addressdetails": 1,
        "countrycodes": "ke",
        "viewbox": "-1.444,36.650,-1.150,37.103",
        "bounded": 1,
    }
    headers = {"User-Agent": "cake_delivery_nairobi/1.0"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        resp.raise_for_status()
        results = resp.json()
        if not results:
            params.pop("viewbox", None)
            params.pop("bounded", None)
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            resp.raise_for_status()
            results = resp.json()
        return [
            {
                "display_name": r.get("display_name", ""),
                "lat": float(r.get("lat", 0)),
                "lng": float(r.get("lon", 0)),
                "place_id": r.get("place_id", ""),
            }
            for r in results
        ]
    except Exception as exc:
        print(f"[nominatim] Suggestion error: {exc}")
        return []


# ── Store finder ──────────────────────────────────────────────────────────────

def find_nearest_store(customer_lat: float, customer_lon: float) -> tuple:
    """
    Find the nearest active store using the Haversine formula.

    Returns (store_instance, distance_km) or (None, None).
    """
    active_stores = Store.objects.filter(is_active=True)
    if not active_stores.exists():
        return None, None

    nearest_store, min_dist = None, float("inf")
    for store in active_stores:
        d = calculate_distance_haversine(
            customer_lat, customer_lon,
            float(store.latitude), float(store.longitude),
        )
        if d < min_dist:
            min_dist = d
            nearest_store = store

    return nearest_store, min_dist


# ── Main entry point ──────────────────────────────────────────────────────────

def get_delivery_details(
    store_lat: float,
    store_lon: float,
    customer_address: str,
    customer_lat: float | None = None,
    customer_lng: float | None = None,
) -> dict:
    """
    Calculate distance and fare from a store to a customer location.

    Resolution order:
      1. If customer coords are already known → skip geocoding.
      2. Try Google Geocoding API.
      3. Fall back to Nominatim.

    Distance resolution order:
      1. Google Distance Matrix API (real road km).
      2. Haversine × 1.25 road-factor (fallback).

    Returns a dict with keys:
        distance_km, fare, decoded_address, customer_lat, customer_lng, method
    """
    decoded_address = customer_address

    # ── Step 1: resolve customer coordinates ──────────────────────────────────
    if customer_lat is None or customer_lng is None:
        loc = geocode_with_google(customer_address)
        if loc is None:
            loc = geocode_with_nominatim(customer_address)
        if loc is None:
            return {
                "distance_km": None,
                "fare": None,
                "decoded_address": customer_address,
                "customer_lat": None,
                "customer_lng": None,
                "method": "error",
            }
        customer_lat   = loc["lat"]
        customer_lng   = loc["lng"]
        decoded_address = loc["display_name"]

    # ── Step 2: get driving distance ──────────────────────────────────────────
    road_km = get_road_distance_google(store_lat, store_lon, customer_lat, customer_lng)

    if road_km is not None:
        method = "google_maps"
    else:
        # Haversine + 25 % road factor
        straight = calculate_distance_haversine(
            store_lat, store_lon, customer_lat, customer_lng
        )
        road_km = straight * 1.25
        method  = "haversine_estimated"

    return {
        "distance_km":    round(road_km, 2),
        "fare":           calculate_fare(road_km),
        "decoded_address": decoded_address,
        "customer_lat":   customer_lat,
        "customer_lng":   customer_lng,
        "method":         method,
    }
