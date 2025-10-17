# ruff: noqa: PLR0913

import enum
import pathlib
import shutil
import webbrowser
from contextlib import AbstractContextManager
from types import TracebackType
from typing import Any, Literal, Self, cast

import click
import google.auth
import httpx
import msal.token_cache
import platformdirs
from google.auth import credentials, exceptions
from yaspin import yaspin

import s2v.client.viz
from s2v.client.auth import AzureCredentials, FileTokenCache
from s2v.client.lib import DEFAULT_URL, S2VClient, ValidationFailure, ValidationMessage
from s2v.version import version


class AuthMode(enum.StrEnum):
    NONE = "none"
    AUTO = "auto"
    USER = "user"


class S2VConfig(AbstractContextManager["S2VConfig"]):
    def __init__(self, config_dir: pathlib.Path):
        self.config_dir = config_dir
        self.token_cache = FileTokenCache(config_dir / "token_cache.json")
        self.credentials_config_path = config_dir / "credentials.json"

    def __enter__(self) -> Self:
        self.token_cache.__enter__()
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> Literal[False]:
        return self.token_cache.__exit__(exc_type, exc_val, exc_tb)


def _setup_credentials(
    auth_mode: AuthMode,
    token_cache: msal.token_cache.TokenCache | None = None,
    credentials_config_path: pathlib.Path | None = None,
) -> credentials.Credentials | None:
    match auth_mode:
        case AuthMode.AUTO:
            if credentials_config_path and credentials_config_path.exists():
                return AzureCredentials.from_file(credentials_config_path, token_cache=token_cache)
            adc, _ = google.auth.default()
            return cast(credentials.Credentials, adc)
        case AuthMode.USER:
            if credentials_config_path is None:
                msg = "credentials_config_path is a mandatory parameter for user auth"
                raise ValueError(msg)
            if not credentials_config_path.exists():
                msg = "Please log in first."
                raise click.ClickException(msg)
            return AzureCredentials.from_file(credentials_config_path, token_cache=token_cache)
        case _:
            return None


def print_validation_message(msg: ValidationMessage) -> None:
    output = ""

    level_color = "yellow" if msg["logging_level"] == "WARNING" else "red"
    output += "["
    output += click.style(msg["logging_level"], fg=level_color, bold=True)
    output += "] "

    if file := msg["file"]:
        output += click.style(file, fg="cyan")
        if line := msg["line"] > 0:
            output += f":{line}"
            if col := msg["column"] > 0:
                output += f":{col}"
        output += ": "

    if msg_type := msg["message_type"]:
        output += f"{msg_type}:"

    output += msg["message"]

    click.echo(output)


class _URLParamType(click.ParamType):
    name = "URL"

    def convert(self, value: Any, param: click.Parameter | None, ctx: click.Context | None) -> httpx.URL:
        try:
            return httpx.URL(value)
        except (TypeError, httpx.InvalidURL) as err:
            self.fail(f"{value!r} is not a valid {self.name}: {err}", param, ctx)


class MutuallyExclusiveOptionError(click.UsageError):
    def __init__(self, options: list[str]):
        self.mutually_exclusive_options = options
        message = (
            "Only one of the following options can be provided: "
            f"{', '.join(['--' + opt.replace('_', '-') for opt in options])}"
        )
        super().__init__(message)


@click.group(name="s2v", help=f"Stream2Vault CLI {version}")
@click.option(
    "--config-dir",
    help="Path to user configuration directory",
    type=click.Path(file_okay=False, path_type=pathlib.Path),
    default=platformdirs.user_config_path("s2v-client"),
    show_default=True,
)
@click.pass_context
def cli(ctx: click.Context, config_dir: pathlib.Path) -> None:
    ctx.obj = ctx.with_resource(S2VConfig(config_dir))


mutually_exclusive_options = ["deploy_objects_opt", "deploy_objects_except_opt"]

input_dir_opt = click.option(
    "-i",
    "--input",
    type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path),
    required=True,
    help="Path to the input directory",
)
output_dir_opt = click.option(
    "-o",
    "--output",
    type=click.Path(file_okay=False, writable=True, path_type=pathlib.Path),
    required=True,
    help="Path to the output directory",
)
information_schema_path_opt = click.option(
    "--information-schema-path",
    type=click.Path(dir_okay=False, exists=True, path_type=pathlib.Path),
    help="Path to the information schema file",
)
data_vault_settings_path_opt = click.option(
    "--data-vault-settings-path",
    type=click.Path(dir_okay=False, exists=True, path_type=pathlib.Path),
    help="Path to the data vault settings file",
)
source_system_settings_path_opt = click.option(
    "--source-system-settings-path",
    type=click.Path(dir_okay=False, exists=True, path_type=pathlib.Path),
    help="Path to the source system settings file",
)
include_objects_opt = click.option(
    "--include-objects",
    type=click.STRING,
    required=False,
    help="List of objects to process, separated by commas",
)
exclude_objects_opt = click.option(
    "--exclude-objects",
    type=click.STRING,
    required=False,
    help="List of objects to exclude from processing, separated by commas",
)
url_opt = click.option(
    "-u",
    "--url",
    type=_URLParamType(),
    default=DEFAULT_URL,
    show_default=True,
    help="URL of the S2V server to connect to",
)
auth_mode_opt = click.option(
    "--auth-mode",
    type=click.Choice(list(AuthMode), case_sensitive=False),
    default=AuthMode.AUTO,
    show_default=True,
    help="How to authenticate to the server",
)


@cli.command("validate", help="Validate vault model")
@input_dir_opt
@url_opt
@auth_mode_opt
@information_schema_path_opt
@data_vault_settings_path_opt
@source_system_settings_path_opt
@include_objects_opt
@exclude_objects_opt
@click.pass_obj
def validate(
    s2v_config: S2VConfig,
    input: pathlib.Path,
    url: httpx.URL,
    auth_mode: AuthMode,
    information_schema_path: pathlib.Path | None,
    data_vault_settings_path: pathlib.Path | None,
    source_system_settings_path: pathlib.Path | None,
    include_objects: str | None,
    exclude_objects: str | None,
) -> None:
    option_count = sum(1 for opt in mutually_exclusive_options if locals().get(opt) is not None)
    if option_count > 1:
        raise MutuallyExclusiveOptionError(mutually_exclusive_options)
    try:
        creds = _setup_credentials(auth_mode, s2v_config.token_cache, s2v_config.credentials_config_path)
        with S2VClient.create(creds, url) as client, yaspin(text="Validating"):
            result = client.validate(
                input,
                information_schema_path,
                data_vault_settings_path,
                source_system_settings_path,
                include_objects,
                exclude_objects,
            )
    except BaseException as err:
        raise click.ClickException(str(err)) from err

    print_validation_message(
        ValidationMessage(
            logging_level="WARNING",
            message=f" {version}. Make sure you are using a version consistent with your workflow.",
            message_type="client version",
            processing_stage=None,
            file=None,
            line=-1,
            column=-1,
        )
    )
    for msg in result.messages:
        print_validation_message(msg)

    if isinstance(result, ValidationFailure):
        raise click.exceptions.Exit(1)
    else:
        click.secho("Success! The model is valid.", fg="green")


@cli.command("generate", help="Generate deployment artifacts for vault model")
@input_dir_opt
@output_dir_opt
@url_opt
@auth_mode_opt
@information_schema_path_opt
@data_vault_settings_path_opt
@source_system_settings_path_opt
@include_objects_opt
@exclude_objects_opt
@click.option("--override", is_flag=True, help="Remove the output directory before writing generated files to it")
@click.pass_obj
def generate(
    s2v_config: S2VConfig,
    input: pathlib.Path,
    output: pathlib.Path,
    url: httpx.URL,
    auth_mode: AuthMode,
    override: bool,
    information_schema_path: pathlib.Path | None,
    data_vault_settings_path: pathlib.Path | None,
    source_system_settings_path: pathlib.Path | None,
    include_objects: str | None,
    exclude_objects: str | None,
) -> None:
    option_count = sum(1 for opt in mutually_exclusive_options if locals().get(opt) is not None)
    if option_count > 1:
        raise MutuallyExclusiveOptionError(mutually_exclusive_options)

    if output.exists():
        if override or click.confirm(f"Remove output directory '{output}'?", prompt_suffix=" "):
            shutil.rmtree(output)
        else:
            click.secho("Fail: Output directory already exists.", fg="red")
            raise click.exceptions.Exit(2)

    try:
        creds = _setup_credentials(auth_mode, s2v_config.token_cache, s2v_config.credentials_config_path)
        with S2VClient.create(creds, url) as client, yaspin(text="Generating") as spinner:
            result = client.generate(
                input,
                output,
                information_schema_path,
                data_vault_settings_path,
                source_system_settings_path,
                include_objects,
                exclude_objects,
            )
            spinner.ok("✅")
    except BaseException as err:
        raise click.ClickException(str(err)) from err

    for msg in result.messages:
        print_validation_message(msg)

    if isinstance(result, ValidationFailure):
        raise click.exceptions.Exit(1)


@cli.command("login", help="Authorize the S2V CLI to access the S2V service")
@click.option(
    "-c",
    "--config",
    type=click.Path(dir_okay=False, path_type=pathlib.Path),
    required=True,
    help="Path to your auth config file",
)
@click.pass_obj
def login(s2v_config: S2VConfig, config: pathlib.Path) -> None:
    try:
        azure_creds = AzureCredentials.from_file(config, token_cache=s2v_config.token_cache)
        azure_creds.login()
    except exceptions.GoogleAuthError as err:
        raise click.ClickException(str(err)) from err
    s2v_config.config_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config, s2v_config.credentials_config_path)
    click.secho("Login successful.", fg="green")


@cli.command("logout", help="Remove all cached credentials")
@click.pass_obj
def logout(s2v_config: S2VConfig) -> None:
    if not s2v_config.credentials_config_path.exists():
        click.secho("Please log in first.", fg="red")
        raise click.exceptions.Exit(1)

    try:
        azure_creds = AzureCredentials.from_file(s2v_config.credentials_config_path, token_cache=s2v_config.token_cache)
        azure_creds.logout()
    except BaseException as err:
        raise click.ClickException(str(err)) from err
    s2v_config.credentials_config_path.unlink()
    click.secho("Logout successful.", fg="green")


@cli.command("visualize", help="Serve a visualization of the specified model (beta)")
@input_dir_opt
def visualize(input: pathlib.Path) -> None:
    s2v.client.viz.visualize(input)


@cli.command("version", help="Print the Stream2Vault CLI's version")
def print_version() -> None:
    click.echo(version)


@cli.command("docs", help="Browse the web documentation")
def browse_docs() -> None:
    try:
        webbrowser.open(str(DEFAULT_URL.join("/")))
    except BaseException as err:
        raise click.ClickException(str(err)) from err


def main() -> None:
    terminal_size = shutil.get_terminal_size()
    cli(auto_envvar_prefix="S2V", max_content_width=terminal_size.columns)
