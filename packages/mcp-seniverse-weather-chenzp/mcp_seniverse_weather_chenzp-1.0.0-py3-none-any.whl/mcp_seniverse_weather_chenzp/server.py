import os
from typing import Any, List, Dict
import requests
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("Weather")
@mcp.tool()
def current_weather(city: str) -> List[Dict[str, Any]]:
    """Query the current weather by city name"""
    # api_key = os.getenv("WEATHER_API_KEY")
    api_key = "SL5s6U5EaM0lroVdF"
    if not api_key:
        raise ValueError("WEATHER_API_KEY environment variable not set")
    try:
        weather_response = requests.get(
            "https://api.seniverse.com/v3/weather/now.json",
            params={"key": api_key,
                    "location": city,
                    "language": "zh-Hans",
                    "units": "c",
                    }
        )
        weather_response.raise_for_status()
        data = weather_response.json()
        results = data["results"]
        if not results:
            return [{"error": f"Could not find weather data for city: {city}"}]
        return results
    except requests.exceptions.RequestException as e:
        error_message = f"Weather API error: {str(e)}"
        if hasattr(e, "response") and e.response is not None:
            try:
                error_data = e.response.json()
                if 'message' in error_data:
                    error_message = f"Weather API error: {error_data['message']}"
            except ValueError:
                pass
        return [{"error": error_message}]