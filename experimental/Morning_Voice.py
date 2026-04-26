import requests
from playsound import playsound
from datetime import datetime
from gnews import GNews
import time
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
# VOICEVOX
VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021")
SPEAKER_ID = int(os.getenv("VOICEVOX_SPEAKER_ID", "47"))
# OpenWeatherMap
API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
LATITUDE = float(os.getenv("OPENWEATHER_LAT", "36.08"))
LONGITUDE = float(os.getenv("OPENWEATHER_LON", "140.076"))
# Raspi Google Calendar Flask endpoint
BASE_URL = os.getenv("CALENDAR_EVENTS_BASE_URL", "http://127.0.0.1:5000/events/")
SCHEDULE_SOURCES = [item.strip() for item in os.getenv("MORNING_SCHEDULE_SOURCES", "3Schedule,4Job,5Univ").split(",") if item.strip()]

def speak(text):
    print(f"[INFO] Creating .wav: {text}")
    response = requests.post(f"{VOICEVOX_URL}/audio_query", params={"text": text, "speaker": SPEAKER_ID}, timeout=30)
    query = response.json()
    query["speedScale"] = 1.0
    query["intonationScale"] = 0.8
    response = requests.post(f"{VOICEVOX_URL}/synthesis", json=query, params={"speaker": SPEAKER_ID}, timeout=30)
    filename = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    with open(filename, "wb") as f:
        f.write(response.content)
    print(f"[INFO] Playing .wav: {filename}")
    playsound(filename)

def get_datetime_info():
    now = datetime.now()
    weekday_jp = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    date_text = f"おはようございます。今日は、{now.month}月{now.day}日、{weekday_jp[now.weekday()]}。時刻は{now.strftime('%H時 %M分')}です。"
    return date_text

def get_weather_info():
    if not API_KEY:
        return "OpenWeather APIキーが未設定のため、天気情報を取得できません。"

    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "appid": API_KEY,
        "units": "metric",
        "lang": "ja"
    }
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    weather_data = response.json()
    today = datetime.now().date()

    temps = []
    pops = []
    high_rain_times = []

    for forecast in weather_data["list"]:
        forecast_time = datetime.strptime(forecast["dt_txt"], "%Y-%m-%d %H:%M:%S")
        if forecast_time.date() == today:
            temp = forecast["main"]["temp"]
            pop = forecast.get("pop", 0) * 100
            hour = forecast_time.hour

            temps.append(temp)
            pops.append(pop)

            if pop > 40:
                time_str = f"{hour}時から"
                high_rain_times.append(f"{time_str}{pop:.0f}%")

    if not temps:
        return "今日の天気情報を取得できませんでした。"

    if high_rain_times:
        rain_warning = "残念ながら、今日は雨が降る可能性があります。"
        rain_times = f"{'、'.join(high_rain_times)}の降水確率です。"
    else:
        rain_warning = "今日は雨の心配は いりません。"
        rain_times = ""

    max_temp = max(temps)
    min_temp = min(temps)

    return (
        f"{rain_warning} {rain_times} "
        f"今日の最高気温は{max_temp:.0f}度、最低気温は{min_temp:.0f}度の予想です。"
    )


def format_time_naturally(time_str):
    dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S%z")
    if dt.minute == 0:
        return f"{dt.hour}時から、"
    else:
        return f"{dt.hour}時{dt.minute}分から、"

def get_schedule_info():
    today = datetime.now().strftime("%Y-%m-%d")
    all_events = []

    for calendar_id in SCHEDULE_SOURCES:
        url = f"{BASE_URL}{calendar_id}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            events = response.json()

            for event in events:
                start_datetime = event["start"]
                start_date = start_datetime.split("T")[0]

                if start_date == today:
                    formatted_time = format_time_naturally(start_datetime)
                    all_events.append(f"{formatted_time} {event['summary']}")

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] {calendar_id} の取得に失敗: {e}")

    if all_events:
        return f"今日は、{'。 '.join(all_events)} の予定があります。"
    else:
        return "今日は、予定がありません。"

def get_news():
    google_news = GNews(language="ja", country="JP", period="1d", max_results=5)
    articles = google_news.get_news_by_topic("business")
    return articles

def morning_announcement():
    time.sleep(1)
    speak("システム、起動")
    #time.sleep(5)
    #speak(get_datetime_info())
    #speak(get_weather_info())
    #speak(get_schedule_info())
    #for news in get_news():
    #    speak(news['title'])
    #print("部屋の電気アナウンス")
    #print("部屋の温度・湿度、エアコンの設定")
    #print("laptop PC,smartphoneの充電状況")
    #print("routineの予定開始と終了時刻のアナウンス")
    #print("部屋の電気消灯アナウンス")
    #print("desktopパソコンの自動シャットダウンとおやすみ")
    #print("AIによる座右の銘と意味の読み上げ")
    #print("直近のイベント情報(有用なサイトを探す必要あり)")
    #print("最初起動時に同時並列で音声データ前を作成しておく")

if __name__ == "__main__":
    morning_announcement()
