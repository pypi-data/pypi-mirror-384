from pathlib import Path
from typing import Callable

from loguru import logger

from exactpy.auth import Auth
from exactpy.models.account import Account


class Client:
    account = Account.set_as_property()

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        cache_callable: Callable | None = Auth.cache_creds,
        cache_callable_kwargs: dict = {"cache_path": Path("./creds.json")},
        base_url: str = "https://start.exactonline.nl/api",
        auth_url: str | None = None,
        access_token_url: str | None = None,
        endpoints_url: str | None = None,
        verbose: bool = True,
    ):
        """An Exact Online Python client.

        Args:
            client_id (str): The Exact Online app registration client ID.
            client_secret (str): The Exact Online app registration client secret.
            cache_callable (Callable, optional): The Callable to use to store the credentials. It must have argument token_dict of type dict.
                If unset (None), no caching will be done. Defaults to exactpy.Auth.cache_creds.
            cache_callable_kwargs (dict): Extra args to pass to cache_callable.
                Defaults to { "cache_path": Path("./creds.json") } but can be customized when e.g. no path is needed.
            base_url (str, optional): The API base url. Defaults to "https://start.exactonline.nl/api".
            auth_url (str | None, optional): The auth base url. Defaults to None. If unset (None), it will be derived from base_url.
            access_token_url (str | None, optional): _description_. Defaults to None. If unset (None), it will be derived from base_url.
            endpoints_url (str | None, optional): the v1 endpoints url. Defaults to None. If unset (None), it will be derived from base_url
            verbose (bool, optional): _description_. Defaults to True.
        """

        self.client_id = client_id
        self.client_secret = client_secret
        self.verbose = verbose

        if cache_callable is not None:
            self.cache_callable = cache_callable
            self.cache_callable_kwargs = cache_callable_kwargs

        self.base_url = base_url.rstrip("/")
        if not self.base_url.endswith("api"):
            raise ValueError("base_url does not end in api, cannot proceed.")

        if auth_url is None:
            self.auth_url = f"{self.base_url}/oauth2/auth"
            if verbose:
                logger.info(
                    f"auth_url was not set. Derived from base_url: {self.auth_url}"
                )
        self.auth_url = self.auth_url.rstrip("/")

        if access_token_url is None:
            self.access_token_url = f"{self.base_url}/oauth2/token"
            if verbose:
                logger.info(
                    f"access_token_url was not set. Derived from base_url: {self.access_token_url}"
                )
        self.access_token_url = self.access_token_url.rstrip("/")
