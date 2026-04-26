import argparse
import datetime
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    openweather_api_key: str
    latitude: float
    longitude: float
    calendar_id: str
    token_file: Path
    credentials_file: Path
    timezone: str
    forecast_hours: int
    slot_hours: int
    replace_after_hours: int
    event_prefix: str
    language: str


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def load_settings() -> Settings:
    return Settings(
        openweather_api_key=_required_env("OPENWEATHER_API_KEY"),
        latitude=float(os.getenv("OPENWEATHER_LAT", "36.083")),
        longitude=float(os.getenv("OPENWEATHER_LON", "140.076")),
        calendar_id=os.getenv("GOOGLE_CALENDAR_ID", "primary").strip(),
        token_file=Path(os.getenv("GOOGLE_CALENDAR_TOKEN_FILE", "token.json")),
        credentials_file=Path(os.getenv("GOOGLE_CALENDAR_OAUTH_CREDENTIALS", "credentials.json")),
        timezone=os.getenv("WEATHER_TIMEZONE", "Asia/Tokyo"),
        forecast_hours=int(os.getenv("WEATHER_FORECAST_HOURS", "24")),
        slot_hours=int(os.getenv("WEATHER_SLOT_HOURS", "3")),
        replace_after_hours=int(os.getenv("WEATHER_REPLACE_AFTER_HOURS", "3")),
        event_prefix=os.getenv("WEATHER_EVENT_PREFIX", "[Weather]").strip(),
        language=os.getenv("OPENWEATHER_LANG", "en").strip(),
    )


def authenticate_google_calendar(token_file: Path, credentials_file: Path):
    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
            creds = flow.run_local_server(port=0)
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(creds.to_json(), encoding="utf-8")

    return build("calendar", "v3", credentials=creds)


def get_weather_color(description: str) -> int:
    text = description.lower()
    if "clear" in text:
        return 7
    if "few clouds" in text or "broken clouds" in text or "scattered clouds" in text:
        return 0
    if "overcast" in text:
        return 8
    if "rain" in text:
        return 9
    return 10


def get_weather_forecast(settings: Settings):
    response = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={
            "lat": settings.latitude,
            "lon": settings.longitude,
            "appid": settings.openweather_api_key,
            "units": "metric",
            "lang": settings.language,
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()

    max_items = max(1, settings.forecast_hours // 3)
    return data.get("list", [])[:max_items]


def delete_existing_weather_events(service, settings: Settings, now_utc: datetime.datetime) -> None:
    time_min = (now_utc + datetime.timedelta(hours=settings.replace_after_hours)).isoformat()
    time_max = (now_utc + datetime.timedelta(hours=settings.forecast_hours)).isoformat()

    events_result = (
        service.events()
        .list(
            calendarId=settings.calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    for event in events:
        summary = event.get("summary", "")
        if not summary.startswith(settings.event_prefix):
            continue
        service.events().delete(calendarId=settings.calendar_id, eventId=event["id"]).execute()
        logging.info("Deleted old weather event: %s", summary)


def create_weather_event(service, settings: Settings, start_time: datetime.datetime, description: str, temperature: float) -> None:
    end_time = start_time + datetime.timedelta(hours=settings.slot_hours)
    summary = f"{settings.event_prefix} {description} / {temperature:.1f}C"
    event = {
        "summary": summary,
        "start": {"dateTime": start_time.isoformat(), "timeZone": settings.timezone},
        "end": {"dateTime": end_time.isoformat(), "timeZone": settings.timezone},
        "colorId": str(get_weather_color(description)),
    }
    service.events().insert(calendarId=settings.calendar_id, body=event).execute()
    logging.info("Created event: %s", summary)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync OpenWeather forecast into Google Calendar.")
    parser.add_argument("--hours", type=int, help="Forecast hours to import (overrides WEATHER_FORECAST_HOURS)")
    args = parser.parse_args()

    settings = load_settings()
    if args.hours is not None and args.hours > 0:
        settings = Settings(**{**settings.__dict__, "forecast_hours": args.hours})

    tz = ZoneInfo(settings.timezone)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    service = authenticate_google_calendar(settings.token_file, settings.credentials_file)

    forecasts = get_weather_forecast(settings)
    delete_existing_weather_events(service, settings, now_utc)

    for item in forecasts:
        start_time_local = datetime.datetime.fromtimestamp(item["dt"], tz=datetime.timezone.utc).astimezone(tz)
        temperature = float(item.get("main", {}).get("temp", 0.0))
        description = item.get("weather", [{}])[0].get("description", "unknown")
        create_weather_event(service, settings, start_time_local, description, temperature)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main()
