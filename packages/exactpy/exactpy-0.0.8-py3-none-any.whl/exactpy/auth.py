from time import time

from requests_oauthlib import OAuth2Session

from exactpy.exceptions import TokenRefreshError


class Auth:
    @classmethod
    def cache_creds(cls):
        pass

    @classmethod
    def parse_response_url(cls):
        pass

    def __init__(self, client_id: str, client_secret: str, redirect_url: str):
        """_summary_

        Args:
            client_id (str): _description_
            client_secret (str): _description_
            redirect_url (str): _description_
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_url = redirect_url
        # self.token_url = token_url
        # self.auth_url = auth_url
        self.token_info = {}

    def acquire_token(self, redirect_response_url: str):
        """Acquire token in a fresh state.

        Args:
            redirect_response_url (str): The reponse url after calling the authorization endpoint.
        """
        _, state = Auth.parse_response_url(redirect_response_url)
        oauth_session = OAuth2Session(
            client_id=self.client_id, state=state, redirect_uri=self.redirect_uri
        )
        oauth_session.fetch_token(
            self.token_url,
            client_secret=self.client_secret,
            authorization_response=redirect_response_url,
        )

        return {
            "access_token": oauth_session._client.access_token,
            "refresh_token": oauth_session._client.refresh_token,
            "expires_on": int(time() + oauth_session._client.expires_in),
        }

    def refresh_token(self):
        """Attemp to refresh access token using the refresh token."""
        refresh_token = {
            "access_token": self._token_info["access_token"],
            "refresh_token": self._token_info["refresh_token"],
            "token_type": "Bearer",
            "expires_in": "-30",
        }
        oauth_session = OAuth2Session(client_id=self.client_id, token=refresh_token)
        try:
            oauth_session.refresh_token(
                url=self.token_url,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
        except Exception:
            raise TokenRefreshError(
                "Token could not be refreshed. Exception message: {e}"
            )

    def is_token_refresh_needed(self):
        return self._token_info.get("expires_on", 0) - time() < 30
