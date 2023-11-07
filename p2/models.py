from pydantic import BaseModel
from typing import Optional, List

class WeatherFactModel(BaseModel):
    temp: float
    pressure_mm: float
    wind_speed: float


class PartModel(BaseModel):
    part_name: str
    temp_min: float
    temp_max: float
    temp_avg: float
    feels_like: float
    icon: str
    condition: str
    daytime: str
    polar: Optional[bool] = None
    wind_speed: float
    wind_gust: float
    wind_dir: str
    pressure_mm: float
    pressure_pa: float
    humidity: float
    prec_mm: float
    prec_period: float
    prec_prob: float


class WeatherForecastModel(BaseModel):
    date: str
    date_ts: int
    week: int
    sunrise: Optional[str] = None
    sunset: Optional[str] = None
    moon_code: int
    moon_text: str
    parts: List[PartModel]

class WeatherResponseModel(BaseModel):
    fact: WeatherFactModel
    forecast: WeatherForecastModel