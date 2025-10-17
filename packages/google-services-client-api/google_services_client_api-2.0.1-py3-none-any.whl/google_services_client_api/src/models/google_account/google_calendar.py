from ...utils.token_validator import ensure_valid_token
from google_services_client_api.src.utils import setup_logger

import datetime as dt
from dateutil import parser

log = setup_logger()


class GoogleCalendar():
    """
    Class for interacting with the Google Calendar API.

    It relies on the `@ensure_valid_token` decorator to inject a valid `self._service`
    for interacting with the Google Calendar API.

    Methods:
        calendar_list_next_events(event_count: int) -> list:
            Lists the next upcoming events from the primary calendar.

        calendar_create_event(summary: str, start_date_time: datetime, end_date_time: datetime, **keyargs) -> None:
            Creates a new event on the user's calendar with optional customization via keyword arguments.
    """
    def __init__(self, service, user_token):
        self._service = service
        self._user_token = user_token


    @ensure_valid_token
    def list_events(
        self, event_count: int = 10, 
        start_date_time: dt.datetime = None, 
        end_date_time: dt.datetime = None
    ) -> list[any]:
        """
        Lists events from the user's Google Calendar, optionally within a date range.

        Decorators:
            @ensure_valid_token: Ensures that `self._service` is an authenticated calendar service.

        Args:
            event_count (int, optional): Maximum number of events to retrieve. Defaults to 
            start_date_time (datetime, optional): Start of the time range to fetch events. Defaults to now if not provided.
            end_date_time (datetime, optional): End of the time range to fetch events.

        Returns:
            list: List of event summaries with their start times. Also prints them to the console.
        """
        log.debug(f'Getting up to {event_count} events...')
        log.debug(
            f'Filtering events from [{start_date_time.strftime("%Y-%m-%d %H:%M") if start_date_time else "now"}] '
            f'to [{end_date_time.strftime("%Y-%m-%d %H:%M") if end_date_time else "..."}]',
        )

        time_min = (start_date_time or dt.datetime.now()).isoformat() + 'Z'
        time_max = end_date_time.isoformat() + 'Z' if end_date_time else None

        query_params = {
            'calendarId': 'primary',
            'timeMin': time_min,
            'maxResults': event_count,
            'singleEvents': True,
            'orderBy': 'startTime'
        }

        if time_max:
            query_params['timeMax'] = time_max

        events_result = self._service.events().list(**query_params).execute()
        events = events_result.get('items', [])

        if not events:
            log.debug('No events found.')
            return []

        log.debug('{')
        for event in events:
            start_raw = event['start'].get('dateTime', event['start'].get('date'))

            try:
                start_dt = parser.isoparse(start_raw)
                start_fmt = start_dt.strftime('%d/%m/%Y %H:%M')
            except Exception:
                start_fmt = start_raw  # fallback se quebrar

            log.debug(f'{start_fmt}: {event.get("summary", "No title")}')
        log.debug('}')

        return events


    @ensure_valid_token
    def create_event(
        self, summary: str, 
        start_date_time: dt.datetime, 
        end_date_time: dt.datetime, 
        **keyargs) -> None:
        """
        Creates a Google Calendar event with a given summary, start and end datetime.

        Additional optional parameters can be passed using keyword arguments to customize
        the event, such as location, description, attendees, reminders, and recurrence rules.

        Decorators:
            @ensure_valid_token: Ensures that `self._service` is an authenticated calendar service.

        Args:
            summary (str): Title of the event.
            start_date_time (datetime): Start time of the event.
            end_date_time (datetime): End time of the event.

        Keyword Args:
            location (str): Location of the event.
            description (str): Description of the event.
            color_id (str): Calendar color ID (1-11).
            timezone (str): Timezone of the event. Default is 'America/Sao_Paulo'.
            attendees_emails (list[str]): Email addresses to invite.
            use_default_reminders (bool): Whether to use default reminders.
            reminder_method (str): 'email' or 'popup' (used if not using default reminders).
            reminder_minutes (int): Minutes before event for reminder.
            recurrence_frequency (str): FREQ value for recurrence (e.g., 'DAILY').
            recurrence_count (int): Number of repetitions for the event.

        Returns:
            None: Prints the link to the created event and its keys.
        """
        log.debug(f'Creating event: {summary}')
        
        timezone = keyargs.get('timezone', 'America/Sao_Paulo')
        
        reminders = ({
                'useDefault': True
            }
            if keyargs.get('use_default_reminders', True)
            else {
                'useDefault': False,
                'overrides': [{
                    'method': keyargs.get('reminder_method', 'email'),
                    'minutes': keyargs.get('reminder_minutes', 24 * 60)
                }]
            }
        )
        
        event = {
            'summary': summary,
            'location': keyargs.get('location', ''),
            'description': keyargs.get('description', ''),
            'start': {
                'dateTime': start_date_time.isoformat(),
                'timeZone': timezone
            },
            'end': {
                'dateTime': end_date_time.isoformat(),
                'timeZone': timezone
            },
            'recurrence': (
                [f'RRULE:FREQ={keyargs["recurrence_frequency"]};COUNT={keyargs["recurrence_count"]}']
                if keyargs.get('recurrence_frequency') and keyargs.get('recurrence_count')
                else []
            ),
            'attendees': [
                {'email': email} for email in keyargs.get('attendees_emails', [])
            ],
            'colorId': keyargs.get('color_id', '2'),
            'reminders': reminders,
        }

        event = self._service.events().insert(calendarId='primary', body=event).execute()
        log.debug(f'Event created: {event.get("htmlLink")}')