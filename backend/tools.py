# tools.py
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from datetime import datetime, timedelta
import json
from functools import partial
from typing import Optional
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


geolocator = Nominatim(user_agent="Wanderbot") 

geocode_city = RateLimiter(geolocator.geocode, min_delay_seconds=1.1, swallow_exceptions=True, return_value_on_exception=None)

def recursively_convert_to_dict(obj):
    if isinstance(obj, dict):
        return {k: recursively_convert_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [recursively_convert_to_dict(elem) for elem in obj]
    elif hasattr(obj, 'items') and callable(obj.items()) and not isinstance(obj, (str, bytes)):
        return {k: recursively_convert_to_dict(v) for k, v in obj.items()}
    else:
        return obj



# Geocoding Function 
def get_coordinates_from_city(city_name: str) -> Optional[dict]:
    try:
        location = geocode_city(city_name)
        if location:
            return {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "name": location.address.split(',')[0].strip(), 
                "full_address": location.address,
            }
        return None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Geocoding error for '{city_name}': {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during geocoding for '{city_name}': {e}")
        return None


# get_weather_forecast with geocoding integration
def get_weather_forecast(city: str, country: str, start_date: str, end_date: str) -> dict:
    full_location = f"{city}, {country}"
    location_data = get_coordinates_from_city(full_location)


    if not location_data:
        return {"error": f"Could not find geographic coordinates for '{city}'. Please check the city name or provide a more specific location."}

    latitude = location_data["latitude"]
    longitude = location_data["longitude"]
    resolved_city_name = location_data.get("name", city) 


    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        if start_dt > end_dt:
            return {"error": "Start date cannot be after end date."}
        today = datetime.utcnow().date()
        if start_dt.date() < today:
             return {"error": f"Start date {start_date} is in the past. Please provide a future or current date."}

        if (end_dt - start_dt).days > 16: 
            return {"error": "Forecast period too long. Please request up to 16 days."}

    except ValueError:
        return {"error": "Invalid date format. Please use YYYY-MM-DD."}

    try:
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        openmeteo = openmeteo_requests.Client(session=retry_session)

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,weather_code",
            "start_date": start_date,
            "end_date": end_date,
            "timezone": "auto"
        }
        responses = openmeteo.weather_api(url, params=params)

        response = responses[0]

        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_weather_code = hourly.Variables(1).ValuesAsNumpy()

        temp_summary = {
            "min_temp": float(hourly_temperature_2m.min()),
            "max_temp": float(hourly_temperature_2m.max()),
            "avg_temp": round(float(hourly_temperature_2m.mean()), 1)
        }

        weather_conditions = {
            "clear": False, "cloudy": False, "rain": False, "snow": False, "fog": False
        }
        for code in hourly_weather_code:
            if code == 0:
                weather_conditions["clear"] = True
            elif 1 <= code <= 3:
                weather_conditions["cloudy"] = True
            elif 45 <= code <= 48:
                weather_conditions["fog"] = True
            elif 51 <= code <= 67:
                weather_conditions["rain"] = True
            elif 71 <= code <= 77:
                weather_conditions["snow"] = True

        dominant_weather = "mixed"
        if weather_conditions["rain"]:
            dominant_weather = "rainy"
        elif weather_conditions["snow"]:
            dominant_weather = "snowy"
        elif weather_conditions["clear"] and not weather_conditions["cloudy"] and not weather_conditions["fog"]:
            dominant_weather = "clear"
        elif weather_conditions["cloudy"]:
            dominant_weather = "cloudy"

        result = {
            "city": resolved_city_name,
            "latitude": latitude, 
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "temperature_summary_celsius": temp_summary,
            "dominant_weather_condition": dominant_weather,
        }

        final_result = recursively_convert_to_dict(result)


        return final_result


    except Exception as e:
        return {"error": f"Failed to fetch weather forecast for {resolved_city_name or city} at {latitude},{longitude}: {str(e)}"}
