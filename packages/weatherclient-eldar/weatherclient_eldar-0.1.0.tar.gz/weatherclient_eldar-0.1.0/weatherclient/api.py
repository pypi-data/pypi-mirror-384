import requests

class WeatherClient:
    """Weather API Client"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5/"

    def get_current_weather(self, city: str):
        """Cari hava vəziyyətini qaytarır"""
        url = f"{self.base_url}weather?q={city}&appid={self.api_key}&units=metric"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code}")
        return response.json()

    def get_forecast(self, city: str, days: int = 5):
        """Gələcək hava proqnozu"""
        url = f"{self.base_url}forecast?q={city}&cnt={days*8}&appid={self.api_key}&units=metric"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code}")
        return response.json()
