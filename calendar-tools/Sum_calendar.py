"""Summarize Google Calendar usage by calendar for a specific date."""

import argparse
import logging
import os
from datetime import datetime, timedelta, timezone

import matplotlib.pyplot as plt
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
JST = timezone(timedelta(hours=9))


def authenticate_google_calendar(service_account_file: str):
    try:
        creds = Credentials.from_service_account_file(service_account_file, scopes=SCOPES)
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        logging.error(f"API auth error: {e}")
        return None


def read_calendar_list(file_path: str):
    calendar_dict = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if "," not in line:
                    continue
                name, calendar_id = line.strip().split(",", 1)
                if name and calendar_id:
                    calendar_dict[name] = calendar_id
        return calendar_dict
    except Exception as e:
        logging.error(f"Error reading calendar list: {e}")
        return {}


def fetch_calendar_events(service, calendar_dict, target_date):
    try:
        start_of_day = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=JST)
        end_of_day = start_of_day + timedelta(days=1)
        calendar_time = {}

        for calendar_name, calendar_id in calendar_dict.items():
            events_result = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=start_of_day.astimezone(timezone.utc).isoformat(),
                    timeMax=end_of_day.astimezone(timezone.utc).isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            for event in events:
                if "dateTime" in event.get("start", {}) and "dateTime" in event.get("end", {}):
                    start = datetime.fromisoformat(event["start"]["dateTime"])
                    end = datetime.fromisoformat(event["end"]["dateTime"])
                    duration = (end - start).total_seconds() / 3600
                    calendar_time[calendar_name] = calendar_time.get(calendar_name, 0) + duration

        return calendar_time
    except Exception as e:
        logging.error(f"Error fetching calendar events: {e}")
        return {}


def plot_calendar_usage(calendar_usage, target_date):
    if not calendar_usage:
        logging.info(f"No events found on {target_date.date()}")
        return

    total_hours = sum(calendar_usage.values())
    total_hours_int = int(total_hours)
    total_minutes = int(round((total_hours - total_hours_int) * 60))

    print(f"\nDate: {target_date.date()} Total: {total_hours_int}h {total_minutes}m")
    for name, hours in sorted(calendar_usage.items(), key=lambda x: x[1], reverse=True):
        h = int(hours)
        m = int(round((hours - h) * 60))
        print(f" - {name}: {h}h {m}m")

    sorted_usage = sorted(calendar_usage.items(), key=lambda x: x[1], reverse=True)
    labels = [item[0] for item in sorted_usage]
    sizes = [item[1] for item in sorted_usage]

    plt.figure(figsize=(10, 6))
    plt.barh(labels, sizes, color="skyblue")
    plt.xlabel("Hours")
    plt.title(f"Calendar Usage on {target_date.date()}")
    plt.gca().invert_yaxis()
    plt.grid(axis="x", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Summarize calendar usage by date.")
    parser.add_argument(
        "--service-account-file",
        default=os.getenv("GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE", "service_account.json"),
        help="Path to service account JSON key",
    )
    parser.add_argument(
        "--calendar-list-file",
        default=os.getenv("GOOGLE_CALENDAR_LIST_FILE", "calendar_list.txt"),
        help="CSV-like file with 'name,calendar_id' per line",
    )
    parser.add_argument(
        "--date",
        help="Target date in YYYY-MM-DD (default: yesterday in JST)",
    )
    args = parser.parse_args()

    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=JST)
    else:
        now_jst = datetime.now(JST)
        target_date = now_jst - timedelta(days=1)

    service = authenticate_google_calendar(args.service_account_file)
    if not service:
        return

    calendar_dict = read_calendar_list(args.calendar_list_file)
    if not calendar_dict:
        logging.error("Calendar list is empty or unreadable.")
        return

    calendar_usage = fetch_calendar_events(service, calendar_dict, target_date)
    plot_calendar_usage(calendar_usage, target_date)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
