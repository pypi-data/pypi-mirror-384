from google_services_client_api.src.models.service_handler import TokenManager, TokenParser, OAuthService
from google_services_client_api.src.models.google_account import GoogleAccount
from google_services_client_api.src.settings import Config
from google_services_client_api.src.utils import setup_logger

log = setup_logger()


class GoogleAccountFactory():
    def __init__(self, client_secrets: str, enable_logs: bool = None):
        """
        Factory to create GoogleAccount instances using a shared client secret (OAuth client).

        Args:
            client_secrets (str | dict): OAuth client secrets or path to secrets JSON file.
            enable_logs (bool): If True, enables debug/info logging.
        """
        self._oauth_service = OAuthService(client_secrets)

        Config.update_configs({
            'enable_logs': enable_logs
        })

    def is_valid_token(self, user_token) -> bool:
        log.info('Consulting token validity:')
        return TokenManager.is_valid_token(user_token)
    
    def generate_authorization_url(self, redirect_uri: str) -> tuple[str, str]:
        """
        Creates a link to authenticate the user.

        Args:
            name (str): Account identifier.
            redirect_uri (str): callback URL.
        
        Returns:
            tuple[str, str]: The authentication URL and the state.
        """
        log.info('Creating OAuth link...')
        
        return self._oauth_service.generate_authorization_url(redirect_uri)
    
    def fetch_token_from_redirect(self, redirected_url, expected_state = None):
        """
        Fetches the token from the redirected URL after user authentication.

        Args:
            redirected_url (str): URL after user authentication.
            expected_state (str, optional): Expected state parameter from the authorization URL.
            
        Returns:
            Credentials: The user's credentials.
        """
        log.info(f'Fetching token from redirect...')
        
        return self._oauth_service.fetch_token_from_redirect(redirected_url, expected_state)
    

    def load_account(self, name: str, user_token: any) -> GoogleAccount:
        """
        Creates a new GoogleAccount instance with valid credentials.

        Args:
            name (str): Account identifier.
            user_token (str | dict | Credentials, optional): Path, dict or Credentials instance for the user token.

        Returns:
            GoogleAccount
        """
        log.info(f'Loading account \'{name}\' and parsing token:')
        
        try:
            user_token = TokenParser.parse_to_credentials(user_token)
        except:
            raise ValueError('Cannot load account without a user_token (path, dict, or Credentials).')

        account = GoogleAccount(
            name=name,
            user_token=user_token
        )
        
        log.info('Account loaded successfully!')
        return account