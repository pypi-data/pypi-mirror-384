from google_services_client_api.src.settings import Packages


import json

# Google Cloud lib
from google_auth_oauthlib.flow import Flow

class OAuthService:
    def __init__(self, client_secrets: str, scopes: list[str] = None):
        self._flows: dict[str, Flow] = {}
        self.client_secrets = self._load_client_secrets(client_secrets)
        
        # Packages
        self.SCOPES = scopes or Packages.SCOPES
    
    def generate_authorization_url(self, redirect_uri: str) -> tuple[str, str]:
        """
        Creates a link to authenticate the user.

        Args:
            name (str): Account identifier.
            redirect_uri (str): callback URL.
        
        Returns:
            tuple[str, str]: The authentication URL and the state.
        """
        flow = self._create_flow(redirect_uri)
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        self._flows[state] = flow
        return auth_url, state
        
    def fetch_token_from_redirect(self, redirected_url, expected_state=None):
        flow = self._flows.pop(expected_state, None)
        if flow is None:
            raise ValueError(f"Invalid or expired OAuth state received: {expected_state}")

        flow.fetch_token(authorization_response=redirected_url)
        return flow.credentials
        
    def _create_flow(self, redirect_uri) -> Flow:
        return Flow.from_client_config(
            self.client_secrets,
            scopes=self.SCOPES,
            redirect_uri=redirect_uri
        )
        
    def _load_client_secrets(self, client_secrets: str | dict) -> dict:
        if isinstance(client_secrets, str):
            try:
                with open(client_secrets, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                raise FileNotFoundError(f'Client secrets file not found: {client_secrets}.')
                
        if isinstance(client_secrets, dict):
            return client_secrets

        raise TypeError(f'Client secrets must be a path or a dict, not {type(client_secrets)}.')
    