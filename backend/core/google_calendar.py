import json
from datetime import timedelta
from typing import Any, Dict
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from django.conf import settings
from django.utils import timezone

from .models import SpecialistDetails


GOOGLE_OAUTH_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_OAUTH_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_CALENDAR_EVENTS_URL = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'


class GoogleCalendarError(Exception):
    pass


def _request_json(url: str, method: str = 'GET', data: Dict[str, Any] | None = None, headers: Dict[str, str] | None = None) -> Dict[str, Any]:
    payload = None
    request_headers = headers or {}
    if data is not None:
        payload = json.dumps(data).encode('utf-8')
        request_headers['Content-Type'] = 'application/json'

    req = Request(url=url, data=payload, method=method, headers=request_headers)

    try:
        with urlopen(req, timeout=20) as response:
            body = response.read().decode('utf-8')
            if not body:
                return {}
            return json.loads(body)
    except HTTPError as exc:
        body = exc.read().decode('utf-8') if exc.fp else ''
        raise GoogleCalendarError(f'Google API error ({exc.code}): {body}') from exc
    except URLError as exc:
        raise GoogleCalendarError(f'Google API connection error: {exc.reason}') from exc


def is_google_oauth_configured() -> bool:
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET and settings.GOOGLE_OAUTH_REDIRECT_URI)


def build_google_auth_url(state: str) -> str:
    if not is_google_oauth_configured():
        raise GoogleCalendarError('Google OAuth is not configured on the server.')

    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
        'response_type': 'code',
        'scope': ' '.join(settings.GOOGLE_OAUTH_SCOPES),
        'access_type': 'offline',
        'prompt': 'consent',
        'include_granted_scopes': 'true',
        'state': state,
    }
    return f"{GOOGLE_OAUTH_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    if not is_google_oauth_configured():
        raise GoogleCalendarError('Google OAuth is not configured on the server.')

    payload = {
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
        'grant_type': 'authorization_code',
    }
    form_payload = urlencode(payload).encode('utf-8')

    req = Request(
        url=GOOGLE_OAUTH_TOKEN_URL,
        data=form_payload,
        method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )

    try:
        with urlopen(req, timeout=20) as response:
            body = response.read().decode('utf-8')
            return json.loads(body)
    except HTTPError as exc:
        body = exc.read().decode('utf-8') if exc.fp else ''
        raise GoogleCalendarError(f'Failed to exchange code for tokens: {body}') from exc


def store_tokens_on_specialist(specialist: SpecialistDetails, token_data: Dict[str, Any]) -> None:
    access_token = token_data.get('access_token', '')
    refresh_token = token_data.get('refresh_token', '')
    expires_in = int(token_data.get('expires_in', 0) or 0)

    specialist.google_access_token = access_token
    if refresh_token:
        specialist.google_refresh_token = refresh_token
    specialist.google_token_expiry = timezone.now() + timedelta(seconds=expires_in) if expires_in else None
    specialist.google_calendar_connected = bool(specialist.google_access_token)
    specialist.save(
        update_fields=[
            'google_access_token',
            'google_refresh_token',
            'google_token_expiry',
            'google_calendar_connected',
        ]
    )


def _refresh_access_token(specialist: SpecialistDetails) -> str:
    if not specialist.google_refresh_token:
        raise GoogleCalendarError('No refresh token available for Google Calendar.')

    payload = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'refresh_token': specialist.google_refresh_token,
        'grant_type': 'refresh_token',
    }
    form_payload = urlencode(payload).encode('utf-8')

    req = Request(
        url=GOOGLE_OAUTH_TOKEN_URL,
        data=form_payload,
        method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )

    try:
        with urlopen(req, timeout=20) as response:
            body = json.loads(response.read().decode('utf-8'))
            specialist.google_access_token = body.get('access_token', specialist.google_access_token)
            expires_in = int(body.get('expires_in', 0) or 0)
            specialist.google_token_expiry = timezone.now() + timedelta(seconds=expires_in) if expires_in else None
            specialist.google_calendar_connected = bool(specialist.google_access_token)
            specialist.save(update_fields=['google_access_token', 'google_token_expiry', 'google_calendar_connected'])
            return specialist.google_access_token
    except HTTPError as exc:
        body = exc.read().decode('utf-8') if exc.fp else ''
        raise GoogleCalendarError(f'Failed to refresh Google access token: {body}') from exc


def get_valid_access_token(specialist: SpecialistDetails) -> str:
    if not specialist.google_access_token:
        raise GoogleCalendarError('Google Calendar is not connected.')

    if specialist.google_token_expiry and specialist.google_token_expiry <= timezone.now() + timedelta(minutes=1):
        return _refresh_access_token(specialist)

    return specialist.google_access_token


def create_google_calendar_event(specialist: SpecialistDetails, event_payload: Dict[str, Any]) -> Dict[str, Any]:
    token = get_valid_access_token(specialist)
    headers = {
        'Authorization': f'Bearer {token}',
    }
    return _request_json(
        url=GOOGLE_CALENDAR_EVENTS_URL,
        method='POST',
        data=event_payload,
        headers=headers,
    )
