"""Create Google Calendar events with OAuth credentials.

Examples:
  python Add_event_cmd.py --summary "Gym" --start "2026-04-27 19:00" --end "2026-04-27 20:00"
  python Add_event_cmd.py --summary "Study" --start "2026-04-27T21:00:00+09:00" --minutes 90
"""

import argparse
import datetime
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
DEFAULT_TIMEZONE = "Asia/Tokyo"


def authenticate_google_calendar(token_file: str, credentials_file: str):
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def parse_datetime(value: str) -> datetime.datetime:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            parsed = datetime.datetime.strptime(value, fmt)
            if parsed.tzinfo is None:
                return parsed
            return parsed.astimezone(datetime.timezone.utc).astimezone()
        except ValueError:
            continue
    raise ValueError(
        "Invalid datetime format. Use 'YYYY-MM-DD HH:MM' or ISO-8601 (e.g. 2026-04-27T19:00:00+09:00)."
    )


def add_event(service, summary: str, start_time: datetime.datetime, end_time: datetime.datetime, calendar_id: str):
    event = {
        "summary": summary,
        "start": {"dateTime": start_time.isoformat(), "timeZone": DEFAULT_TIMEZONE},
        "end": {"dateTime": end_time.isoformat(), "timeZone": DEFAULT_TIMEZONE},
    }
    service.events().insert(calendarId=calendar_id, body=event).execute()
    print(f"Added event: {summary} ({start_time} - {end_time})")


def main():
    parser = argparse.ArgumentParser(description="Add an event to Google Calendar.")
    parser.add_argument("--summary", required=True, help="Event title")
    parser.add_argument("--start", required=True, help="Start datetime")
    parser.add_argument("--end", help="End datetime")
    parser.add_argument("--minutes", type=int, help="Duration in minutes (used when --end is omitted)")
    parser.add_argument(
        "--calendar-id",
        default=os.getenv("GOOGLE_CALENDAR_ID", "primary"),
        help="Target calendar ID",
    )
    parser.add_argument(
        "--token-file",
        default=os.getenv("GOOGLE_CALENDAR_TOKEN_FILE", "token.json"),
        help="Path to OAuth token JSON",
    )
    parser.add_argument(
        "--credentials-file",
        default=os.getenv("GOOGLE_CALENDAR_OAUTH_CREDENTIALS", "credentials.json"),
        help="Path to OAuth client credentials JSON",
    )
    args = parser.parse_args()

    start_time = parse_datetime(args.start)
    if args.end:
        end_time = parse_datetime(args.end)
    elif args.minutes:
        end_time = start_time + datetime.timedelta(minutes=args.minutes)
    else:
        raise ValueError("Specify either --end or --minutes.")

    service = authenticate_google_calendar(args.token_file, args.credentials_file)
    add_event(service, args.summary, start_time, end_time, args.calendar_id)


if __name__ == "__main__":
    main()
