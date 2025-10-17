from google.oauth2.credentials import Credentials
import os
# Local
from google_services_client_api.src.utils import setup_logger

log = setup_logger()


class TokenParser:
    @staticmethod
    def parse_to_credentials(raw_token: any) -> Credentials:
        if isinstance(raw_token, Credentials):
            log.debug('Loading token as Credentials object...')
            return raw_token
        
        if isinstance(raw_token, str): 
            log.debug('Loading token as JSON file...')
            return Credentials.from_authorized_user_file(raw_token)
        
        if isinstance(raw_token, dict):
            log.debug('Loading token as dict...')
            return Credentials.from_authorized_user_info(raw_token)
            
        raise TypeError(f"Token type {type(raw_token)} not supported. Must be str (path), dict, or Credentials object.")


class TokenManager:
    @classmethod
    def is_valid_token(cls, user_token) -> bool:
        """
        Checks if the current credentials token is valid.

        Returns:
            bool: True if the token is valid, False otherwise.
        """
        try:
            return cls.load_token(user_token).valid
        except:
            return False

    @classmethod
    def load_token(self, file_path: str) -> Credentials | None:
        """Carrega o token do disco, se existir e for válido."""
        if os.path.exists(file_path):
            return None

        try:
            credentials = TokenParser.parse_to_credentials(file_path)
            log.info(f"Token loaded from {file_path}")
            return credentials
        except Exception as e:
            log.warning(f"Failed to load token from disk ({file_path}): {e}")
            return None

    @staticmethod
    def save_token(creds: Credentials, file_path: str) -> None:
        """Salva o objeto Credentials no formato JSON no caminho especificado."""
        try:
            with open(file_path, 'w') as token_file:
                 token_file.write(creds.to_json())
            log.info(f"Token salvo com sucesso em: {file_path}")
        except Exception as e:
            log.error(f"Falha ao salvar token: {e}")