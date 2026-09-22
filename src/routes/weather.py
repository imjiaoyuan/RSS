import json
from datetime import datetime, timedelta, timezone

from utils import fetch_url

ROUTE_CONFIG = {
    "url": "https://api.open-meteo.com/v1/forecast",
    "air_url": "https://air-quality-api.open-meteo.com/v1/air-quality",
    "cities": [
        {"name": "成都", "slug": "Chengdu", "latitude": 30.5728, "longitude": 104.0668},
        {"name": "敦煌", "slug": "Dunhuang", "latitude": 40.1421, "longitude": 94.6620},
    ],
    "forecast_days": 3,
}

WMO_CODES = {
    0: "晴", 1: "基本晴", 2: "局部多云", 3: "阴",
    45: "雾", 48: "雾凇",
    51: "轻毛毛雨", 53: "毛毛雨", 55: "浓毛毛雨",
    56: "冻毛毛雨", 57: "冻毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻雨", 67: "强冻雨",
    71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
    80: "小阵雨", 81: "阵雨", 82: "强阵雨",
    85: "小阵雪", 86: "大阵雪",
    95: "雷阵雨", 96: "雷阵雨伴冰雹", 99: "强雷雨伴冰雹",
}


def _sky(code):
    return WMO_CODES.get(code, f"天气码{code}")


def _round(value):
    return round(value) if isinstance(value, (int, float)) else value


def _aqi_level(aqi):
    if aqi <= 50:
        return "优"
    if aqi <= 100:
        return "良"
    if aqi <= 150:
        return "轻度污染"
    if aqi <= 200:
        return "中度污染"
    if aqi <= 300:
        return "重度污染"
    return "严重污染"


def _fetch_air(url, city):
    query = (
        f"?latitude={city['latitude']}&longitude={city['longitude']}"
        "&current=us_aqi,pm2_5&timezone=Asia%2FShanghai"
    )
    try:
        cur = json.loads(fetch_url(url + query))["current"]
        aqi = cur.get("us_aqi")
        pm25 = cur.get("pm2_5")
        if aqi is None:
            return ""
        pm_part = f"，PM2.5 {_round(pm25)}" if pm25 is not None else ""
        return f"，AQI {_round(aqi)}（{_aqi_level(_round(aqi))}{pm_part}）"
    except Exception as e:
        raise RuntimeError(f"air quality for {city['name']}: {e}")


def fetch(config):
    china_tz = timezone(timedelta(hours=8))
    now = datetime.now(timezone.utc)
    china_dt = now.astimezone(china_tz)

    articles = []
    for city in config["cities"]:
        query = (
            f"?latitude={city['latitude']}&longitude={city['longitude']}"
            "&current=temperature_2m,apparent_temperature,relative_humidity_2m,"
            "weather_code,wind_speed_10m"
            "&daily=temperature_2m_max,temperature_2m_min,weather_code,"
            "precipitation_sum,precipitation_probability_max,uv_index_max,sunrise,sunset"
            "&timezone=Asia%2FShanghai&forecast_days=1"
        )
        data = json.loads(fetch_url(config["url"] + query))
        cur = data["current"]
        day = data["daily"]

        today = (
            f"{_sky(cur['weather_code'])} {_round(cur['temperature_2m'])}°C"
            f"（体感 {_round(cur['apparent_temperature'])}°C）"
        )
        title = (
            f"{city['name']}：{today}，今日 {_round(day['temperature_2m_min'][0])}"
            f"~{_round(day['temperature_2m_max'][0])}°C，"
            f"降水 {_round(day['precipitation_sum'][0])}mm"
            f"（{day['precipitation_probability_max'][0]}%），"
            f"湿度 {cur['relative_humidity_2m']}%，"
            f"风速 {_round(cur['wind_speed_10m'])}km/h，"
            f"UV {_round(day['uv_index_max'][0])}，"
            f"日出 {day['sunrise'][0][11:16]} / 日落 {day['sunset'][0][11:16]}"
            f"{_fetch_air(config['air_url'], city)}"
        )

        articles.append({
            'title': title,
            'link': f"https://wttr.in/{city['slug']}",
            'published_dt': now,
            'date_str': china_dt.strftime('%Y-%m-%d'),
            'time_str': china_dt.strftime('%H:%M'),
        })

    return articles
