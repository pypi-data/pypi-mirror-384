from google.auth.transport.requests import Request
from googleapiclient.discovery import build
# Local
from google_services_client_api.src.utils.logger import setup_logger

log = setup_logger()


def ensure_valid_token(func):
    """
    ###
    
    Decorator that ensures the wrapped function receives an up to date authenticated Google Calendar API service.

    The wrapped function must accept `service` as its argument or keyargument.
    
    Useful for refreshing, and building of the service client and ensuring the credentials are valid.

    #### Returns:
        The return value of the wrapped function, with an injected `service`.
    """
    def wrapper(self, *args, **kwargs):
        token = self._user_token

        if not token or not token.valid:
            if token and token.expired and token.refresh_token:
                try:
                    token.refresh(self._request_handler) 

                    self._service = build('calendar', 'v3', credentials=token)
                    log.info('Token refreshed successfully.')

                except Exception as e:
                    log.error(f'Failed to refresh token: {e}')
                    raise RuntimeError('Authentication failed: Could not refresh token.')
            else:
                log.error('Invalid credentials and no refresh token available.')
                raise RuntimeError('Invalid credentials and no refresh token available.')

        return func(self, *args, **kwargs)
    return wrapper
