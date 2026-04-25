import datetime
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import discord
from discord.ext import tasks
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/calendar"]
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    discord_token: str
    target_user_id: int
    target_guild_id: int
    service_account_file: str
    calendar_id: str
    log_file: str
    check_interval_seconds: int
    timezone: str


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise ValueError(f"Missing required environment variable: {name}")
    return value.strip()


def load_settings() -> Settings:
    return Settings(
        discord_token=_get_required_env("DISCORD_BOT_TOKEN"),
        target_user_id=int(_get_required_env("DISCORD_TARGET_USER_ID")),
        target_guild_id=int(_get_required_env("DISCORD_TARGET_GUILD_ID")),
        service_account_file=_get_required_env("GOOGLE_SERVICE_ACCOUNT_FILE"),
        calendar_id=_get_required_env("GOOGLE_CALENDAR_ID"),
        log_file=os.getenv("PLAYING_BOT_LOG_FILE", "logs/activity_log.txt"),
        check_interval_seconds=int(os.getenv("PLAYING_BOT_CHECK_INTERVAL_SECONDS", "60")),
        timezone=os.getenv("PLAYING_BOT_TIMEZONE", "Asia/Tokyo"),
    )


def setup_logging(log_file: str) -> None:
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    stream_handler = logging.StreamHandler()

    logging.basicConfig(
        handlers=[file_handler, stream_handler],
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.getLogger("discord").setLevel(logging.WARNING)


intents = discord.Intents.default()
intents.presences = True
intents.members = True
client = discord.Client(intents=intents)

settings: Optional[Settings] = None
member: Optional[discord.Member] = None
google_calendar_service = None
previous_activity_name: Optional[str] = None
previous_time: Optional[datetime.datetime] = None


def authenticate_google_calendar():
    if settings is None:
        raise RuntimeError("Settings are not loaded.")

    try:
        creds = Credentials.from_service_account_file(settings.service_account_file, scopes=SCOPES)
        return build("calendar", "v3", credentials=creds)
    except Exception as exc:
        logging.error("Google Calendar auth error: %s", exc)
        return None


def create_calendar_event(start_time: datetime.datetime, end_time: datetime.datetime, activity_name: str) -> None:
    if google_calendar_service is None or settings is None:
        logging.error("Google Calendar service is not available.")
        return

    try:
        event = {
            "summary": activity_name,
            "start": {"dateTime": start_time.isoformat(), "timeZone": settings.timezone},
            "end": {"dateTime": end_time.isoformat(), "timeZone": settings.timezone},
        }
        google_calendar_service.events().insert(calendarId=settings.calendar_id, body=event).execute()
        logging.info("Calendar event created: %s (%s - %s)", activity_name, start_time, end_time)
    except Exception as exc:
        logging.error("Google Calendar API error: %s", exc)


@tasks.loop(seconds=60)
async def check_activity() -> None:
    global previous_activity_name, previous_time

    if member is None:
        logging.warning("Target member is not ready yet.")
        return

    activity = member.activity
    activity_name = getattr(activity, "name", None)
    current_time = datetime.datetime.now(datetime.timezone.utc)

    if previous_activity_name is None and activity_name:
        logging.info("Activity started: %s", activity_name)
        previous_activity_name = activity_name
        previous_time = current_time
    elif previous_activity_name and activity_name and activity_name != previous_activity_name:
        logging.info("Activity changed: %s -> %s", previous_activity_name, activity_name)
        if previous_time is not None:
            create_calendar_event(previous_time, current_time, previous_activity_name)
        previous_activity_name = activity_name
        previous_time = current_time
    elif previous_activity_name and activity_name is None:
        logging.info("Activity ended: %s", previous_activity_name)
        if previous_time is not None:
            create_calendar_event(previous_time, current_time, previous_activity_name)
        previous_activity_name = None
        previous_time = None


@client.event
async def on_ready() -> None:
    global member, google_calendar_service

    if settings is None:
        logging.error("Settings are not loaded.")
        await client.close()
        return

    guild = client.get_guild(settings.target_guild_id)
    if guild is None:
        logging.error("Guild not found: %s", settings.target_guild_id)
        await client.close()
        return

    member = guild.get_member(settings.target_user_id)
    if member is None:
        try:
            member = await guild.fetch_member(settings.target_user_id)
        except Exception as exc:
            logging.error("Target member fetch failed: %s", exc)
            await client.close()
            return

    google_calendar_service = authenticate_google_calendar()
    if google_calendar_service is None:
        logging.error("Google Calendar authentication failed.")
        await client.close()
        return

    logging.info("Bot ready as %s", client.user)
    if not check_activity.is_running():
        check_activity.start()


def main() -> None:
    global settings
    settings = load_settings()
    setup_logging(settings.log_file)
    check_activity.change_interval(seconds=settings.check_interval_seconds)
    logging.info("Starting PlayingBOT. Monitoring user_id=%s in guild_id=%s", settings.target_user_id, settings.target_guild_id)
    client.run(settings.discord_token)


if __name__ == "__main__":
    main()
