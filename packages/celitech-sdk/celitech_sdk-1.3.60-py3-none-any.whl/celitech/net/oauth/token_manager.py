from typing import Set
from time import time


class OauthToken:
    def __init__(self, access_token: str, scopes: Set[str], expires_at: int):
        self.access_token = access_token
        self.scopes = scopes
        self.expires_at = expires_at


class TokenManager:
    def __init__(self, base_oauth_url: str):
        self._base_oauth_url = base_oauth_url
        self._token = None
        self.client_id = None
        self.client_secret = None

    def set_base_oauth_url(self, base_oauth_url: str):
        """
        Sets the base oAuth URL
        """
        self._base_oauth_url = base_oauth_url
        return self

    def set_client_id(self, client_id: str):
        """
        Sets the client_id.
        """
        self.client_id = client_id
        return self

    def set_client_secret(self, client_secret: str):
        """
        Sets the client_secret.
        """
        self.client_secret = client_secret
        return self

    def get_token(self, scopes: Set[str]) -> OauthToken:
        """
        Get an OAuth token with the given scopes

        :param scopes: The scopes to request
        :type scopes: Set[str]

        :return: The OAuth token
        :rtype: OauthToken
        """
        has_all_scopes = self._token and self._token.scopes.issuperset(scopes)
        valid_token = self._token and (
            self._token.expires_at is None
            or (self._token.expires_at - int(time())) > 5000
        )
        if has_all_scopes and valid_token:
            return self._token

        if self._token:
            scopes.update(self._token.scopes)

        response = self._get_access_token(scopes)
        self._token = OauthToken(
            access_token=response.access_token,
            scopes=scopes,
            expires_at=(
                response.expires_in + int(time())
                if hasattr(response, "expires_in")
                else None
            ),
        )
        return self._token

    def clean(self):
        """
        Clean the token manager to force a new token request
        """
        self._token = None

    def _get_access_token(self, scopes: Set[str]):
        # We need to import the service here, to avoid a circular reference error.
        from ...services.o_auth import OAuthService

        service = OAuthService(base_url=self._base_oauth_url, token_manager=self)
        return service.get_access_token(
            request_body={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        )
