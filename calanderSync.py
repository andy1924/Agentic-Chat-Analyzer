import os
import json
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.events']


def authenticate_google_calendar():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # This requires a credentials.json file from Google Cloud Console
            if not os.path.exists('credentials.json'):
                print("❌ ERROR: Missing 'credentials.json'.")
                print(
                    "Go to Google Cloud Console -> Enable Calendar API -> Create OAuth Client ID -> Download JSON as 'credentials.json'")
                return None

            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)


def sync_reminders_to_calendar():
    service = authenticate_google_calendar()
    if not service:
        return

    # Load your AI-generated JSON
    json_path = os.path.join("mainData", "analyzedResults.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            profiles = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Could not find {json_path}")
        return

    events_created = 0

    for profile in profiles:
        user_name = profile.get("analyzed_user", "Unknown User")
        reminders = profile.get("suggested_reminders", [])

        for reminder in reminders:
            title = reminder.get("event_title", "Untitled Event")
            dt_context = reminder.get("datetime_context", "None")
            desc = reminder.get("description", "")

            # 🛠️ THE SKIP LOGIC: Skip if missing, "None", or not provided
            if not dt_context or str(dt_context).strip().lower() == "none":
                print(f"⏭️  Skipping '{title}' for {user_name} (No time provided)")
                continue

            # We need to ensure the time is in a format Google understands (ISO 8601)
            try:
                # Parse the ISO string (e.g., '2026-03-02T15:00:00+05:30')
                start_time = datetime.datetime.fromisoformat(dt_context.replace('Z', '+00:00'))
                # Default event duration to 1 hour
                end_time = start_time + datetime.timedelta(hours=1)

                event_body = {
                    'summary': f"{title} ({user_name})",
                    'description': desc,
                    'start': {
                        'dateTime': start_time.isoformat(),
                    },
                    'end': {
                        'dateTime': end_time.isoformat(),
                    },
                }

                # Insert the event into the primary calendar
                event = service.events().insert(calendarId='primary', body=event_body).execute()
                print(f"✅ Created: {title} -> {event.get('htmlLink')}")
                events_created += 1

            except ValueError:
                # If the AI gave a text string like "Tomorrow afternoon" instead of an ISO date
                print(f"⚠️  Skipping '{title}' (Invalid time format: {dt_context})")
                continue

    print(f"\n🎉 Sync Complete! Added {events_created} new events to your Google Calendar.")


if __name__ == '__main__':
    sync_reminders_to_calendar()