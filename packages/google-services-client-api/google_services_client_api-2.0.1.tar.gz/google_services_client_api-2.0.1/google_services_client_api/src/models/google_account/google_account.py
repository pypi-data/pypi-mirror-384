from .google_calendar import GoogleCalendar
import datetime as dt

# Google Cloud lib
from googleapiclient.discovery import build

class GoogleAccount:
    """
    GoogleAccount is the main interface for managing a user's Google Calendar and 
    authentication credentials.

    Avaliable methods from:
        - .calendar: Provides calendar-related methods: list_events, create_events, etc.
    """
    calendar: GoogleCalendar

    def __init__(self, name: str, user_token: any = None):
        """
        Initializes a new GoogleAccount instance.

        Args:
            name (str): User or account identifier.
            user_token (any): Existing credentials object (optional).
            credentials (any): Raw credential information or dict (optional).
            logger (any): Logger instance (optional).
        """
        # Personal Info
        self.name = name
        
        # Google-Service-Credentials
        self._user_token = user_token

        # Google-Calendar
        _calendar_service = build('calendar', 'v3', credentials=user_token)
        self.calendar = GoogleCalendar(_calendar_service, user_token)

    def __repr__(self):
        return f"<GoogleAccount name='{self.name}'>"