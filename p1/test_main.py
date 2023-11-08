# test_main.py
from fastapi import HTTPException
from unittest.mock import patch, MagicMock
import pytest
from main import app, get_lat_long, get_weather_data, validate_weather_response, cache
from models import WeatherResponseModel
from fastapi.testclient import TestClient
import pandas as pd
from pydantic import ValidationError

client = TestClient(app)

mock_city_data = pd.DataFrame(
    {"City": ["testcity"], "Latitude": [1.0], "Longitude": [2.0]}
)
mock_weather_data = {
    "fact": {"temp": 20.0, "pressure_mm": 750.0, "wind_speed": 5.0},
    "forecast": {
        "date": "2023-11-08",
        "date_ts": 1667894400,
        "week": 45,
        "sunrise": "07:12",
        "sunset": "16:38",
        "moon_code": 3,
        "moon_text": "Waning crescent",
        "parts": [
            {
                "part_name": "morning",
                "temp_min": 15.0,
                "temp_max": 21.0,
                "temp_avg": 18.0,
                "feels_like": 16.0,
                "icon": "bkn_n",
                "condition": "cloudy",
                "daytime": "d",
                "polar": False,
                "wind_speed": 3.0,
                "wind_gust": 7.0,
                "wind_dir": "nw",
                "pressure_mm": 745.0,
                "pressure_pa": 993.0,
                "humidity": 60.0,
                "prec_mm": 0.0,
                "prec_period": 3.0,
                "prec_prob": 20.0,
            },
        ],
    },
}


def test_get_lat_long_valid_city(monkeypatch):
    monkeypatch.setattr("main.city_df", mock_city_data)
    lat, long = get_lat_long("testcity")
    assert lat == 1.0
    assert long == 2.0


def test_get_lat_long_invalid_city(monkeypatch):
    monkeypatch.setattr("main.city_df", mock_city_data)
    with pytest.raises(HTTPException):
        get_lat_long("invalidcity")


@patch("main.requests.get")
def test_get_weather_data(mock_get):
    cache.clear()
    mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_weather_data)
    response = get_weather_data(1.0, 2.0)
    assert response.status_code == 200
    assert response.json() == mock_weather_data


def test_validate_weather_response_valid_data():
    validate_weather_response(
        MagicMock(status_code=200, json=lambda: mock_weather_data)
    )


def test_validate_weather_response_invalid_data():
    with pytest.raises(ValidationError):
        validate_weather_response(MagicMock(status_code=200, json=lambda: {}))


@patch("main.get_lat_long")
@patch("main.get_weather_data")
def test_get_curr_weather_200(mock_get_weather_data, mock_get_lat_long):
    cache.clear()
    mock_get_lat_long.return_value = (1.0, 2.0)
    mock_get_weather_data.return_value = MagicMock(
        status_code=200, json=lambda: mock_weather_data
    )
    response = client.get("/weather?city=testcity")
    assert response.status_code == 200
    assert response.json() == {"temp": 20, "pressure_mm": 750, "wind_speed": 5}


@patch("main.get_lat_long")
@patch("main.get_weather_data")
def test_get_curr_weather_bad_response(mock_get_weather_data, mock_get_lat_long):
    cache.clear()
    mock_get_lat_long.return_value = (1.0, 2.0)
    mock_get_weather_data.return_value = MagicMock(status_code=500)
    response = client.get("/weather?city=testcity")
    assert response.status_code == 500
    assert response.json() == {"detail": "Error getting weather data"}


@patch("main.get_lat_long")
@patch("main.get_weather_data")
def test_get_weather_forecast(mock_get_weather_data, mock_get_lat_long):
    cache.clear()
    mock_get_lat_long.return_value = (1.0, 2.0)
    mock_get_weather_data.return_value = MagicMock(
        status_code=200, json=lambda: mock_weather_data
    )
    response = client.get("/forecast?city=testcity")
    assert response.status_code == 200
    assert response.json() == mock_weather_data["forecast"]


@patch("main.get_lat_long")
@patch("main.get_weather_data")
def test_get_weather_forecast_bad_response(mock_get_weather_data, mock_get_lat_long):
    cache.clear()
    mock_get_lat_long.return_value = (1.0, 2.0)
    mock_get_weather_data.return_value = MagicMock(status_code=500)
    response = client.get("/forecast?city=testcity")
    assert response.status_code == 500
    assert response.json() == {"detail": "Error getting weather data"}


@patch("main.get_lat_long")
@patch("main.requests.get")
def test_caching(mock_get, mock_get_lat_long):
    cache.clear()
    mock_get_lat_long.return_value = (1.0, 2.0)
    mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_weather_data)
    client.get("/weather?city=testcity")
    assert cache.get((1.0, 2.0)) is not None
