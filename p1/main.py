from fastapi import FastAPI, HTTPException
from cachetools import cached, TTLCache
import requests
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
import os
import pandas as pd
import uvicorn
import logging
from models import *



logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

app = FastAPI()
load_dotenv()

cache = TTLCache(maxsize=1000, ttl=1800)
city_df = pd.read_csv('../city.csv')
city_df['City'] = city_df['City'].str.lower()

def get_lat_long(city):
    city = city.lower()
    if city not in city_df['City'].values:
        raise HTTPException(status_code=422, detail="City not found")
    lat, long = city_df[city_df['City'] == city][['Latitude', 'Longitude']].iloc[0]
    return lat, long

@cached(cache, key=lambda lat, long: (lat, long))
def get_weather_data(lat, long):
    api_url = f"https://api.weather.yandex.ru/v2/informers?lat={lat}&lon={long}&lang=ru_RU"
    response = requests.get(api_url, headers={"X-Yandex-API-Key": os.getenv("YANDEX_API_KEY")})
    return response


def validate_weather_response(response):
    try:
        weather_data = WeatherResponseModel(**response.json())
    except ValidationError as e:
        raise e


@app.get("/weather")
async def get_curr_weather(city: str):
    lat, long = get_lat_long(city)

    response = cache.get((lat, long))
    if not response:
        logger.info(f"Cache miss for {city}")
        response = get_weather_data(lat, long)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error getting weather data")
        try:
            validate_weather_response(response)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    response_json = response.json()
    weather_data = {
        'temp': response_json['fact']['temp'],
        'pressure_mm': response_json['fact']['pressure_mm'],
        'wind_speed': response_json['fact']['wind_speed']
    }

    return weather_data

@app.get("/forecast")
async def get_weather_forecast(city: str):
    lat, long = get_lat_long(city)

    response = cache.get((lat, long))
    if not response:
        logger.info(f"Cache miss for {city}")
        response = get_weather_data(lat, long)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error getting weather data")
        try:
            validate_weather_response(response)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
            
    response_json = response.json()
    
    return response_json['forecast']


if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.error(e)