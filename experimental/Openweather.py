from __future__ import annotations

import os

import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
LATITUDE = float(os.getenv("OPENWEATHER_LAT", "36.08"))
LONGITUDE = float(os.getenv("OPENWEATHER_LON", "140.076"))

def get_weather_info():
    if not API_KEY:
        return "OPENWEATHER_API_KEY が未設定です。"

    url = f'http://api.openweathermap.org/data/2.5/forecast'
    params = {
        'lat': LATITUDE,
        'lon': LONGITUDE,
        'appid': API_KEY,
        'units': 'metric',
        'lang': 'ja'
    }
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    weather_data = response.json()

    today_forecast = weather_data.get('list', [])[:8]
    if not today_forecast:
        return "天気予報データを取得できませんでした。"
    min_temp = float('inf')
    max_temp = float('-inf')
    weather_counts = {}
    total_precip = 0

    for forecast in today_forecast:
        temp = forecast['main']['temp']
        description = forecast['weather'][0]['description']
        precip_prob = forecast.get('pop', 0) * 100  # 降水確率（popは0〜1の値）

        # 最低・最高気温を更新
        min_temp = min(min_temp, temp)
        max_temp = max(max_temp, temp)

        # 天気の種類をカウント
        weather_counts[description] = weather_counts.get(description, 0) + 1

        # 降水確率を合計
        total_precip += precip_prob

    # 最も出現回数の多い天気を選ぶ
    main_weather = max(weather_counts, key=weather_counts.get)

    # 平均降水確率
    avg_precip_prob = total_precip / len(today_forecast)

    # 読み上げ用のテキストを作成
    weather_text = (f"本日の天気予報。天気は {main_weather}。"
                    f"最低気温は {min_temp:.1f} 度、最高気温は {max_temp:.1f} 度。"
                    f"降水確率は {avg_precip_prob:.1f} パーセント。")

    return weather_text


if __name__ == "__main__":
    print(get_weather_info())
