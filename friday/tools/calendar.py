import os
from datetime import datetime, timedelta
from dateutil import parser
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP
from tzlocal import get_localzone
from friday.tools.memory import remember, recall, forget

CREDENTIALS_PATH = "friday/calendar/credentials.json"
TOKEN_PATH = "friday/calendar/token.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]

_calendar_service = None
mcp = FastMCP("friday-calendar")


def _get_calendar_service():
    global _calendar_service
    if _calendar_service is not None:
        return _calendar_service

    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    _calendar_service = build("calendar", "v3", credentials=creds)
    return _calendar_service


def parse_datetime(natural_str: str) -> dict:
    if not natural_str or not natural_str.strip():
        return {"status": "error", "reason": "empty datetime string"}
    try:
        dt = parser.parse(natural_str, fuzzy=True)
        return {"datetime": dt.isoformat(), "status": "ok"}
    except Exception:
        return {"status": "error", "reason": "could not parse datetime"}


@mcp.tool()
def set_reminder(title: str, datetime_str: str) -> dict:
    if not title or not title.strip():
        return {"status": "error", "reason": "empty title"}

    parsed = parse_datetime(datetime_str)
    if parsed["status"] == "error":
        return parsed

    iso_dt = parsed["datetime"]
    mem_result = remember(title, category="reminder", source="voice")
    memory_id = mem_result["memory_id"]

    tz = str(get_localzone())
    end_dt = (datetime.fromisoformat(iso_dt) + timedelta(hours=1)).isoformat()
    event_body = {
        "summary": title,
        "start": {"dateTime": iso_dt, "timeZone": tz},
        "end": {"dateTime": end_dt, "timeZone": tz},
    }

    event_id = None
    status = "set"
    try:
        service = _get_calendar_service()
        event = service.events().insert(calendarId="primary", body=event_body).execute()
        event_id = event.get("id")
    except Exception:
        event_id = None
        status = "set_memory_only"

    return {
        "memory_id": memory_id,
        "event_id": event_id,
        "status": status,
        "title": title,
        "datetime": iso_dt,
    }


@mcp.tool()
def get_reminders(limit: int = 5) -> list[dict]:
    pool = recall("reminder", limit=limit * 2)
    filtered = [r for r in pool if r.get("category") == "reminder"]
    return filtered[:limit]


@mcp.tool()
def cancel_reminder(memory_id: str, event_id: str = None) -> dict:
    forget_result = forget(memory_id)
    if forget_result["status"] == "not_found":
        return {"status": "not_found"}
    if event_id:
        try:
            _get_calendar_service().events().delete(
                calendarId="primary", eventId=event_id
            ).execute()
        except Exception:
            pass
    return {"status": "cancelled", "memory_id": memory_id}
