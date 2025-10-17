from typing import Any, TypedDict, cast

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class WhoAmIResponse(TypedDict, total=False):
    my_email_address: str
    display_name: str
    given_name: str
    family_name: str
    formatted_name: str
    profile_picture_url: str
    google_calendar_access: bool
    calendars_count: int
    timezone: str


def build_who_am_i_response(
    context: Any, calendar_service: Any, oauth_service: Any
) -> WhoAmIResponse:
    """Build complete who_am_i response from Google Calendar, OAuth and People APIs."""
    credentials = Credentials(
        context.authorization.token if context.authorization and context.authorization.token else ""
    )
    people_service = _build_people_service(credentials)
    person = _get_people_api_data(people_service)

    user_info = _extract_profile_data(person)
    user_info.update(_extract_google_calendar_info(calendar_service, oauth_service))

    return cast(WhoAmIResponse, user_info)


def _extract_profile_data(person: dict[str, Any]) -> dict[str, Any]:
    """Extract user profile data from People API response."""
    profile_data = {}

    names = person.get("names", [])
    if names:
        primary_name = names[0]
        profile_data.update({
            "display_name": primary_name.get("displayName"),
            "given_name": primary_name.get("givenName"),
            "family_name": primary_name.get("familyName"),
            "formatted_name": primary_name.get("displayNameLastFirst"),
        })

    photos = person.get("photos", [])
    if photos:
        profile_data["profile_picture_url"] = photos[0].get("url")

    email_addresses = person.get("emailAddresses", [])
    if email_addresses:
        primary_emails = [
            email for email in email_addresses if email.get("metadata", {}).get("primary")
        ]
        if primary_emails:
            profile_data["my_email_address"] = primary_emails[0].get("value")

    return profile_data


def _extract_google_calendar_info(calendar_service: Any, oauth_service: Any) -> dict[str, Any]:
    """Extract Google Calendar specific information."""
    calendar_info: dict[str, Any] = {}

    try:
        # Get calendar list for basic info
        calendars_result = calendar_service.calendarList().list().execute()
        calendars = calendars_result.get("items", [])

        calendar_info["google_calendar_access"] = True
        calendar_info["calendars_count"] = len(calendars)

        # Get primary calendar timezone
        primary_calendars = [cal for cal in calendars if cal.get("primary", False)]
        if primary_calendars:
            primary_cal = primary_calendars[0]
            calendar_info["timezone"] = primary_cal.get("timeZone", "")
        else:
            calendar_info["timezone"] = ""

    except Exception:
        calendar_info["google_calendar_access"] = False
        calendar_info["calendars_count"] = 0
        calendar_info["timezone"] = ""

    return calendar_info


def _build_people_service(credentials: Credentials) -> Any:
    """Build and return the People API service client."""
    return build("people", "v1", credentials=credentials)


def _get_people_api_data(people_service: Any) -> dict[str, Any]:
    """Get user profile information from People API."""
    person_fields = "names,emailAddresses,photos"
    return cast(
        dict[str, Any],
        people_service.people().get(resourceName="people/me", personFields=person_fields).execute(),
    )
