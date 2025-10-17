import abc
import datetime
import io
import pathlib
import tempfile
import typing
import zipfile
from collections.abc import Callable, Iterable, Iterator
from contextlib import AbstractContextManager
from types import TracebackType
from typing import IO, Literal, Self

import httpx
from google.auth import credentials, external_account, impersonated_credentials
from google.auth.transport import requests

from s2v.version import version


def _google_auth(
    source_credentials: credentials.Credentials, audience: str
) -> Callable[[httpx.Request], httpx.Request]:
    if isinstance(source_credentials, external_account.Credentials):
        # External account credentials are not supported in the IDTokenCredentials directly yet.
        # See https://github.com/googleapis/google-auth-library-python/issues/1252
        source_credentials = source_credentials._initialize_impersonated_credentials()  # noqa: SLF001

    id_token_credentials = impersonated_credentials.IDTokenCredentials(source_credentials, audience, include_email=True)
    transport = requests.Request()

    def authenticate(request: httpx.Request) -> httpx.Request:
        id_token_credentials.before_request(transport, request.method, request.url, request.headers)
        return request

    return authenticate


def _zip_directory_contents(dir: pathlib.Path, target: IO[bytes]) -> None:
    """
    Creates a ZIP archive of the given directory's contents, recursively.

    :param dir: the directory to search for contents to be zipped
    :param target: a target IO to write the ZIP archive to
    """

    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for directory, _, files in dir.walk():
            zip_file.write(directory, directory.relative_to(dir))
            for file_name in files:
                file = directory / file_name
                zip_file.write(file, file.relative_to(dir))


class ValidationMessage(typing.TypedDict):
    logging_level: str
    message: str
    message_type: str
    file: str | None
    line: int
    column: int
    processing_stage: str | None


def _bad_request_failure_message(message: str) -> ValidationMessage:
    return ValidationMessage(
        logging_level="ERROR",
        message=message,
        message_type="bad_request",
        file=None,
        line=-1,
        column=-1,
        processing_stage=None,
    )


class ValidationResult(abc.ABC):
    def __init__(self, messages: Iterable[ValidationMessage]) -> None:
        self.messages = messages

    @abc.abstractmethod
    def __bool__(self) -> bool: ...

    def _messages_with_log_level(self, log_level: str) -> Iterator[ValidationMessage]:
        for msg in self.messages:
            if msg["logging_level"] == log_level:
                yield msg

    def warnings(self) -> Iterator[ValidationMessage]:
        return self._messages_with_log_level("WARNING")

    def errors(self) -> Iterator[ValidationMessage]:
        return self._messages_with_log_level("ERROR")


class ValidationSuccess(ValidationResult):
    def __bool__(self) -> Literal[True]:
        return True

    def __str__(self) -> str:
        if not self.messages:
            return "OK"

        num_warnings = sum(1 for _ in self.warnings())
        return f"{num_warnings} warning(s)"


class ValidationFailure(ValidationResult):
    def __bool__(self) -> Literal[False]:
        return False

    def __str__(self) -> str:
        num_errors = sum(1 for _ in self.errors())
        num_warnings = sum(1 for _ in self.warnings())
        return f"{num_errors} error(s), {num_warnings} warning(s)"


_VALIDATE_HEADERS: httpx.Headers = httpx.Headers(
    {"Accept": "application/json", "Accept-Encoding": "gzip", "Content-Type": "application/zip"}
)
_GENERATE_HEADERS: httpx.Headers = httpx.Headers(
    {"Accept": "application/json, application/zip", "Content-Type": "application/zip"}
)


DEFAULT_URL = httpx.URL("https://s2v.reeeliance.com")


class S2VClient(AbstractContextManager["S2VClient"]):
    def __init__(self, client: httpx.Client):
        self._httpx_client = client

    def __enter__(self) -> Self:
        self._httpx_client.__enter__()
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> Literal[False]:
        self._httpx_client.__exit__(exc_type, exc_val, exc_tb)
        return False

    @classmethod
    def create(cls, creds: credentials.Credentials | None, base_url: str | httpx.URL = DEFAULT_URL) -> Self:
        authorization = _google_auth(creds, str(base_url)) if creds else None
        headers = {"User-Agent": f"s2v-client/{version}"}
        timeout = httpx.Timeout(timeout=datetime.timedelta(minutes=5).total_seconds())
        return cls(httpx.Client(base_url=base_url, auth=authorization, headers=headers, timeout=timeout))

    @staticmethod
    def _setup_params(
        input_dir: pathlib.Path,
        information_schema_path: pathlib.PurePath | None,
        data_vault_settings_path: pathlib.PurePath | None,
        source_system_settings_path: pathlib.PurePath | None,
    ) -> dict[str, str]:
        path_params = {
            "information_schema_path": information_schema_path,
            "data_vault_settings_path": data_vault_settings_path,
            "source_system_settings_path": source_system_settings_path,
        }

        return {k: str(v.relative_to(input_dir)) for k, v in path_params.items() if v is not None}

    def validate(
        self,
        input_dir: pathlib.Path,
        information_schema_path: pathlib.Path | None = None,
        data_vault_settings_path: pathlib.Path | None = None,
        source_system_settings_path: pathlib.Path | None = None,
        include_objects: str | None = None,
        exclude_objects: str | None = None,
    ) -> ValidationResult:
        path_params = self._setup_params(
            input_dir,
            information_schema_path,
            data_vault_settings_path,
            source_system_settings_path,
        )
        params = dict(path_params)

        params["include_objects"] = include_objects if include_objects else ""
        params["exclude_objects"] = exclude_objects if exclude_objects else ""

        with tempfile.TemporaryFile(suffix=".zip") as zip_file:
            _zip_directory_contents(input_dir, zip_file)
            zip_file.seek(0)

            response = self._httpx_client.post(
                "/api/v1/validate",
                params=params,
                content=zip_file,
                headers=_VALIDATE_HEADERS,
            )

        json_body = response.json()
        match response.status_code:
            case httpx.codes.OK:
                return ValidationSuccess(json_body)
            case httpx.codes.BAD_REQUEST:
                return ValidationFailure([_bad_request_failure_message(json_body.get("detail"))])
            case httpx.codes.UNPROCESSABLE_ENTITY:
                return ValidationFailure(json_body)
            case _:
                response.raise_for_status()
                # This is unreachable, because raise_for_status() will already raise an error.
                # However, we need to convince the type checker that no return statement is missing.
                raise  # noqa: PLE0704

    def generate(
        self,
        input_dir: pathlib.Path,
        output_dir: pathlib.PurePath,
        information_schema_path: pathlib.Path | None = None,
        data_vault_settings_path: pathlib.Path | None = None,
        source_system_settings_path: pathlib.Path | None = None,
        include_objects: str | None = None,
        exclude_objects: str | None = None,
    ) -> ValidationResult:
        path_params = self._setup_params(
            input_dir,
            information_schema_path,
            data_vault_settings_path,
            source_system_settings_path,
        )
        params = dict(path_params)

        params["include_objects"] = include_objects if include_objects else ""
        params["exclude_objects"] = exclude_objects if exclude_objects else ""
        params["version"] = version

        with tempfile.TemporaryFile(suffix=".zip") as zip_file:
            _zip_directory_contents(input_dir, zip_file)
            zip_file.seek(0)

            response = self._httpx_client.post(
                "/api/v1/generate",
                params=params,
                content=zip_file,
                headers=_GENERATE_HEADERS,
            )

        match response.status_code:
            case httpx.codes.OK:
                with zipfile.ZipFile(io.BytesIO(response.content), "r") as response_zip:
                    response_zip.extractall(output_dir)
                return ValidationSuccess([])
            case httpx.codes.BAD_REQUEST:
                return ValidationFailure([_bad_request_failure_message(response.json().get("detail"))])
            case httpx.codes.UNPROCESSABLE_ENTITY:
                return ValidationFailure(response.json())
            case _:
                response.raise_for_status()
                # This is unreachable, because raise_for_status() will already raise an error.
                # However, we need to convince the type checker that no return statement is missing.
                raise  # noqa: PLE0704
