from pydantic import BaseModel, Field
from typing import List
import json


class WeatherCondition(BaseModel):
    text: str = Field(default="")
    icon: str = Field(default="")
    code: int = Field(default=0)


class WeatherLocation(BaseModel):
    name: str
    region: str
    country: str
    lat: float
    lon: float
    tz_id: str
    localtime_epoch: int
    localtime: str


class WeatherCurrent(BaseModel):
    last_updated_epoch: int
    last_updated: str
    temp_c: float
    temp_f: float
    is_day: int
    condition: WeatherCondition
    wind_mph: float
    wind_kph: float
    wind_degree: int
    wind_dir: str
    pressure_mb: float
    pressure_in: float
    precip_mm: float
    precip_in: float
    humidity: int
    cloud: int
    feelslike_c: float
    feelslike_f: float
    windchill_c: float
    windchill_f: float
    heatindex_c: float
    heatindex_f: float
    dewpoint_c: float
    dewpoint_f: float
    vis_km: float
    vis_miles: float
    uv: float
    gust_mph: float
    gust_kph: float


class WeatherAstro(BaseModel):
    sunrise: str
    sunset: str
    moonrise: str
    moonset: str
    moon_phase: str
    moon_illumination: int
    is_moon_up: int
    is_sun_up: int


class WeatherDay(BaseModel):
    maxtemp_c: float = Field(default=0.0)
    maxtemp_f: float = Field(default=0.0)
    mintemp_c: float = Field(default=0.0)
    mintemp_f: float = Field(default=0.0)
    avgtemp_c: float = Field(default=0.0)
    avgtemp_f: float = Field(default=0.0)
    maxwind_mph: float = Field(default=0.0)
    maxwind_kph: float = Field(default=0.0)
    totalprecip_mm: float = Field(default=0.0)
    totalprecip_in: float = Field(default=0.0)
    totalsnow_cm: float = Field(default=0.0)
    avgvis_km: float = Field(default=0.0)
    avgvis_miles: float = Field(default=0.0)
    avghumidity: int = Field(default=0)
    daily_will_it_rain: int = Field(default=0)
    daily_chance_of_rain: int = Field(default=0)
    daily_will_it_snow: int = Field(default=0)
    daily_chance_of_snow: int = Field(default=0)
    condition: WeatherCondition
    uv: float = Field(default=0.0)


class WeatherHour(BaseModel):
    time_epoch: int
    time: str
    temp_c: float
    temp_f: float
    is_day: int
    condition: WeatherCondition
    wind_mph: float
    wind_kph: float
    wind_degree: int
    wind_dir: str
    pressure_mb: float
    pressure_in: float
    precip_mm: float
    precip_in: float
    snow_cm: float
    humidity: int
    cloud: int
    feelslike_c: float
    feelslike_f: float
    windchill_c: float
    windchill_f: float
    heatindex_c: float
    heatindex_f: float
    dewpoint_c: float
    dewpoint_f: float
    will_it_rain: int
    chance_of_rain: int
    will_it_snow: int
    chance_of_snow: int
    vis_km: float
    vis_miles: float
    gust_mph: float
    gust_kph: float
    uv: float
    short_rad: float
    diff_rad: float


class WeatherForecastDay(BaseModel):
    date: str
    date_epoch: int
    day: WeatherDay
    astro: WeatherAstro
    # hour: List[WeatherHour]


class WeatherForecast(BaseModel):
    forecastday: List[WeatherForecastDay]


class WeatherResponse(BaseModel):
    location: WeatherLocation
    current: WeatherCurrent
    forecast: WeatherForecast

    def filter_for_llm(self):
        data = {
            "location": self.location.name,
            "current": self.current.temp_c,
            "forecast": self.forecast.forecastday[0].day.condition.text,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
