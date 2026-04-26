import argparse
import datetime
import logging
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def authenticate_google_calendar(token_file: str, credentials_file: str):
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(token_file, "w", encoding="utf-8") as token:
                token.write(creds.to_json())
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return None

    try:
        service = build("calendar", "v3", credentials=creds)
        logging.info("Authenticated Google Calendar")
        return service
    except Exception as e:
        logging.error(f"Error authenticating Google Calendar: {e}")
        return None


def delete_events_for_range(service, calendar_id: str, days: int):
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    time_min = now_utc.isoformat()
    time_max = (now_utc + datetime.timedelta(days=days)).isoformat()

    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
        print("No events found in the specified period.")
        return

    for event in events:
        try:
            summary = event.get("summary", "(no title)")
            service.events().delete(calendarId=calendar_id, eventId=event["id"]).execute()
            print(f"Deleted: {summary} (ID: {event['id']})")
        except Exception as e:
            print(f"Failed to delete event ID {event.get('id', 'unknown')}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Delete Google Calendar events in a future time range.")
    parser.add_argument(
        "--calendar-id",
        default=os.getenv("GOOGLE_CALENDAR_ID", "primary"),
        help="Target calendar ID",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=5,
        help="Delete events from now up to this many days ahead",
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

    service = authenticate_google_calendar(args.token_file, args.credentials_file)
    if not service:
        print("Failed to authenticate Google Calendar.")
        return

    delete_events_for_range(service, args.calendar_id, args.days)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
