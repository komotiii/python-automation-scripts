from flask import Flask, jsonify
import datetime
import os
import pytz
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from flask_cors import CORS
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)
load_dotenv()

local_tz = pytz.timezone("Asia/Tokyo")

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE", "service_account.json")
CALENDAR_LIST_FILE = os.getenv("GOOGLE_CALENDAR_LIST_FILE", "calendar_list.txt")
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_calendar_service():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('calendar', 'v3', credentials=creds)

def fetch_calendar_ids(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        calendar_mappings = {}
        for line in file:
            if line.strip():
                parts = line.strip().split(",")
                name, calendar_id = parts
                calendar_mappings[name] = calendar_id
        return calendar_mappings

def fetch_events_for_calendar(calendar_name, calendar_id):
    service = get_calendar_service()
    now = datetime.datetime.now(local_tz)
    start_of_day = local_tz.localize(datetime.datetime(now.year, now.month, now.day, 0, 0, 0))
    end_of_day = local_tz.localize(datetime.datetime(now.year, now.month, now.day + 1, 0, 0, 0))
    start_of_day_utc = start_of_day.astimezone(pytz.utc).isoformat()
    end_of_day_utc = end_of_day.astimezone(pytz.utc).isoformat()
    events_result = service.events().list(
        calendarId=calendar_id, timeMin=start_of_day_utc, timeMax=end_of_day_utc,
        singleEvents=True, orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    all_events = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date')) if 'end' in event else None
        all_events.append({
            'calendar_name': calendar_name,
            'start': start,
            'end': end,
            'summary': event['summary']
        })

    return all_events

@app.route('/events')
def get_all_events():
    calendar_mappings = fetch_calendar_ids(CALENDAR_LIST_FILE)
    all_events = []

    for calendar_name, calendar_id in calendar_mappings.items():
        all_events.extend(fetch_events_for_calendar(calendar_name, calendar_id))

    all_events.sort(key=lambda x: x['start'])
    return jsonify(all_events)


@app.route('/events/<calendar_name>')
def get_calendar_events(calendar_name):
    calendar_mappings = fetch_calendar_ids(CALENDAR_LIST_FILE)

    if calendar_name not in calendar_mappings:
        return jsonify({"error": f"カレンダー '{calendar_name}' は存在しません"}), 404

    events = fetch_events_for_calendar(calendar_name, calendar_mappings[calendar_name])
    return jsonify(events)

if __name__ == '__main__':
    host = os.getenv("CALENDAR_FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("CALENDAR_FLASK_PORT", "5000"))
    app.run(host=host, port=port, debug=False)
