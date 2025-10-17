import requests
from .base import Abcweaatherapi


url = "https://api.open-meteo.com/v1/forecast"

class openmeteo(Abcweaatherapi):
    
    def __init__(self,latitude, longitude,**kwargs):
        self.latitude = latitude
        self.longitude = longitude
    def current_temp(latitude, longitude):
        payload = {
        "latitude": latitude,   # مثال: تهران
        "longitude": longitude,
        "current_weather": True
    }
        response = requests.get(url, params=payload)
        if response.status_code == 200:
            data = response.json()
            if "current_weather" in data:
                temperature = data["current_weather"]["temperature"]
                print(f"Current temperature: {temperature}°C")
                
                