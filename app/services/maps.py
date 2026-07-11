"""
OpenStreetMap integration.

- Geocoding (address -> lat/lng) via the public Nominatim API.
- Routing (lat/lng pair -> distance, duration, polyline) via the public
  OSRM demo server.

Both are free public instances suitable for development and low volume.
For production traffic, self-host Nominatim/OSRM or use a commercial OSM
provider (e.g. LocationIQ, Geoapify, Mapbox) and just swap the base URLs
in config — the function signatures here don't need to change.
"""
import requests
from flask import current_app

REQUEST_TIMEOUT = 6  # seconds — fail fast rather than hang a booking request


def geocode(address: str):
    """Returns {'lat': float, 'lng': float, 'display_name': str} or None."""
    base_url = current_app.config["OSM_NOMINATIM_URL"]
    try:
        resp = requests.get(
            f"{base_url}/search",
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": "MoveX/1.0 (support@movex.app)"},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        results = resp.json()
        if not results:
            return None
        top = results[0]
        return {
            "lat": float(top["lat"]),
            "lng": float(top["lon"]),
            "display_name": top.get("display_name", address),
        }
    except (requests.RequestException, ValueError, KeyError) as exc:
        current_app.logger.warning("Nominatim geocode failed for %r: %s", address, exc)
        return None


def get_route(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng):
    """Returns {'distance_km': float, 'duration_minutes': float, 'geometry': geojson}
    or None if the routing engine is unreachable — callers should fall back
    to the haversine estimate in app/services/pricing.py."""
    base_url = current_app.config["OSRM_ROUTING_URL"]
    coords = f"{pickup_lng},{pickup_lat};{dropoff_lng},{dropoff_lat}"
    try:
        resp = requests.get(
            f"{base_url}/route/v1/driving/{coords}",
            params={"overview": "full", "geometries": "geojson"},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "Ok" or not data.get("routes"):
            return None
        route = data["routes"][0]
        return {
            "distance_km": round(route["distance"] / 1000, 2),
            "duration_minutes": round(route["duration"] / 60, 1),
            "geometry": route["geometry"],
        }
    except (requests.RequestException, ValueError, KeyError) as exc:
        current_app.logger.warning("OSRM routing failed: %s", exc)
        return None
