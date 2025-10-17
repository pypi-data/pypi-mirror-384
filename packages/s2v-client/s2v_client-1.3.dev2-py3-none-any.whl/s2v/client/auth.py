import pathlib
import stat
import typing
import urllib.parse
from collections.abc import Mapping
from contextlib import AbstractContextManager
from os import PathLike
from types import TracebackType
from typing import Any, Literal, Self

import msal.application
import msal.oauth2cli.oidc
import msal.token_cache
from google.auth import exceptions, external_account


class FileTokenCache(msal.token_cache.SerializableTokenCache, AbstractContextManager["FileTokenCache"]):
    def __init__(self, path: pathlib.Path) -> None:
        super().__init__()
        self.path = path

    def __enter__(self) -> Self:
        if self.path.exists():
            with self.path.open() as f:
                self.deserialize(f.read())
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> Literal[False]:
        if self.has_state_changed:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("w") as f:
                f.write(self.serialize())
            self.path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        return False


class AzureCredentials(external_account.Credentials):
    def __init__(self, token_cache: msal.token_cache.TokenCache, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.entra_id_app_id = self._extract_entra_id_app_id(self._credential_source)
        self.entra_id_scopes = [f"{self.entra_id_app_id}/.default"]

        self._app = msal.application.PublicClientApplication(self.entra_id_app_id, token_cache=token_cache)

    def _constructor_args(self) -> Mapping[str, Any]:
        args = super()._constructor_args()
        return {**args, "token_cache": self._app.token_cache}

    @staticmethod
    def _extract_entra_id_app_id(credential_source: Mapping[str, Any]) -> str:
        credential_src_url_str = credential_source.get("url")
        if not credential_src_url_str:
            msg = "'credential_source.url' is missing"
            raise exceptions.MalformedError(msg)

        credential_src_url = urllib.parse.urlparse(credential_src_url_str)
        credential_src_params = urllib.parse.parse_qs(credential_src_url.query)
        resource_param = credential_src_params.get("resource")
        resource = resource_param[0] if resource_param else None
        if not resource:
            msg = "'credential_source.url' is missing the 'resource' parameter"
            raise exceptions.MalformedError(msg)

        try:
            resource_url = urllib.parse.urlparse(resource)
        except ValueError as err:
            msg = "'credential_source.url(resource)' parameter is malformed"
            raise exceptions.MalformedError(msg) from err

        app_id = resource_url.hostname
        if app_id is None:
            msg = "'credential_source.url(resource)' parameter URL hostname part is empty"
            raise exceptions.MalformedError(msg)

        return app_id

    def login(self) -> None:
        match self._app.acquire_token_interactive(
            scopes=self.entra_id_scopes, prompt=msal.oauth2cli.oidc.Prompt.SELECT_ACCOUNT
        ):
            case {"error": error, **kwargs}:
                msg = str(error)
                if kwargs:
                    msg += f": {kwargs}"
                raise exceptions.OAuthError(msg)

    def logout(self) -> None:
        accounts = self._app.get_accounts()
        if not accounts:
            msg = "No logged in user account available."
            raise exceptions.RefreshError(msg)
        for account in accounts:
            self._app.remove_account(account)

    def retrieve_subject_token(self, _: Any) -> str:
        accounts = self._app.get_accounts()
        account = next(iter(accounts), None)
        match self._app.acquire_token_silent_with_error(scopes=self.entra_id_scopes, account=account):
            case {"access_token": access_token} if isinstance(access_token, str):
                return access_token
            case {"error": error, **kwargs}:
                msg = str(error)
                if kwargs:
                    msg += f": {kwargs}"
                raise exceptions.RefreshError(msg)
            case None:
                msg = "No logged in user account available"
                raise exceptions.RefreshError(msg)
            case other:
                msg = f"Cannot parse token response: {other}"
                raise exceptions.MalformedError(msg)

    @classmethod
    def from_file(cls, filename: str | PathLike[str], **kwargs: Any) -> Self:
        return typing.cast(Self, super().from_file(filename, **kwargs))
