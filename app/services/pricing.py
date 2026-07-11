import math


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    """Great-circle distance in kilometers between two lat/lng points.
    Used for fare estimation when a real routing engine (OSRM) call isn't
    available or hasn't returned yet — OSRM's road-network distance is
    preferred when both pickup/dropoff coordinates are geocoded (see
    app/services/maps.py)."""
    if None in (lat1, lng1, lat2, lng2):
        return 0.0
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def estimate_fare(distance_km: float, duration_minutes: float, base_fare, per_km_rate, per_minute_rate):
    """Returns (low, high) fare bounds. A tight +/- band stands in for
    demand-based surge until a real dispatch/pricing service exists."""
    base = float(base_fare) + float(distance_km) * float(per_km_rate) + float(duration_minutes) * float(per_minute_rate)
    low = round(max(base, float(base_fare)), 2)
    high = round(low * 1.35, 2)
    return low, high


def estimate_duration_minutes(distance_km: float, avg_speed_kmh: float = 28.0) -> float:
    """Rough ETA for city traffic when no routing engine duration is
    available. 28 km/h reflects typical mixed urban traffic."""
    if avg_speed_kmh <= 0:
        return 0.0
    return round((distance_km / avg_speed_kmh) * 60, 1)
