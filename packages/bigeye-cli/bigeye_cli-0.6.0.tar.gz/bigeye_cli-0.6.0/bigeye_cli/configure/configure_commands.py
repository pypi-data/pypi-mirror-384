import typer
from rich import print
from rich.table import Table
from rich.text import Text
from typing import List

from bigeye_cli.functions import run_enum_menu, get_workspaces_for_user, get_workspace_id_for_user
from bigeye_cli import global_options

from bigeye_sdk.authentication.enums import AuthConfType, BrowserType
from bigeye_sdk.authentication.api_authentication import BasicAPIAuth, BrowserAPIAuth, ApiAuth, APIKeyAuth
from bigeye_sdk.authentication.config import Config
from bigeye_sdk.client.datawatch_client import get_user_auth, create_api_key_for_configuration
from bigeye_sdk.generated.com.bigeye.models.generated import WorkspaceIdNameAndRole
from bigeye_sdk.exceptions.exceptions import WorkspaceNotSetException

from bigeye_sdk.log import get_logger

log = get_logger(__file__)

app = typer.Typer(no_args_is_help=False, help='Configuration Commands for Bigeye CLI')


@app.callback(invoke_without_command=True)
def configure(
        ctx: typer.Context,
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace
):
    required_config = {}
    if ctx.invoked_subcommand is None:
        """Create a default credential for Bigeye CLI."""
        from rich.prompt import Prompt, Confirm

        use_default_credential = True
        if workspace != 'DEFAULT':
            use_default_credential = Confirm.ask("Should this workspace inherit the default credentials?")

        # If configuring the default workspace or user specifically asked to enter creds, then perform credential
        # workflow
        if workspace == 'DEFAULT' or not use_default_credential:
            auth_type = run_enum_menu(enum_clz=AuthConfType, default=AuthConfType.API_KEY_AUTH)

            if auth_type == AuthConfType.BROWSER_AUTH:
                browser_type = run_enum_menu(enum_clz=BrowserType, default=BrowserType.CHROME)

                browser_profile_user_name = None

                if browser_type == BrowserType.CHROME:
                    # TODO Could condition on path containing Profile_N directories.
                    browser_profile_user_name = Prompt.ask(
                        "Enter the profile email if logged into Chrome (Default: None)")
                base_url = Prompt.ask("Enter the Bigeye URL", default="https://app.bigeye.com")
                cred = BrowserAPIAuth(browser=browser_type, base_url=base_url,
                                      browser_profile_user_name=browser_profile_user_name)

            elif auth_type == AuthConfType.API_KEY_AUTH:
                base_url = Prompt.ask("Enter the Bigeye URL", default="https://app.bigeye.com")
                username = Prompt.ask("Enter Bigeye username")
                uses_sso = Confirm.ask("Do you use SSO to access the Bigeye UI?")
                if not uses_sso:
                    print(Text(text='\n** Please login to continue **', style='bold green'))
                    password = Prompt.ask("Enter Bigeye password for username above")
                    create_key = Confirm.ask("Would you like to create an API Key?")
                    basic_cred = BasicAPIAuth(base_url=base_url,
                                              user=username,
                                              password=password)
                    if create_key:
                        key_name = Prompt.ask("Enter a name for the key")
                        key_description = Prompt.ask("Enter a description (optional)", default="")
                        api_key = create_api_key_for_configuration(
                            cred=basic_cred, name=key_name, description=key_description
                        )
                    else:
                        api_key = Prompt.ask("Enter the API Key")

                    required_config = get_workspaces_for_user(
                        cred=basic_cred, workspace=workspace, use_default_credential=use_default_credential
                    )
                else:
                    print(Text(text='\n** Make sure you have created an API key in the UI **', style='bold green'))
                    api_key = Prompt.ask("Enter the API Key")
                    api_auth = APIKeyAuth(base_url=base_url, api_key=api_key)
                    required_config = get_workspace_id_for_user(cred=api_auth,
                                                                workspace=workspace,
                                                                use_default_credential=use_default_credential,
                                                                bigeye_username=username)


                cred = APIKeyAuth(base_url=base_url, api_key=api_key)

            else:
                base_url = Prompt.ask("Enter the Bigeye URL", default="https://app.bigeye.com")
                username = Prompt.ask("Enter the username")
                password = Prompt.ask("Enter the password")
                cred = BasicAPIAuth(base_url=base_url,
                                    user=username,
                                    password=password)

            cred.save_as_file(auth_filename=bigeye_conf, cred=cred, workspace=workspace)
        # If inheriting from default credential then load default credential
        else:
            cred = ApiAuth.load(auth_file=bigeye_conf, workspace='DEFAULT')

        if not required_config:
            required_config = get_workspaces_for_user(
                cred=cred, workspace=workspace, use_default_credential=use_default_credential
            )

        Config(**required_config).upsert_workspace_config(
            config_file=config_file,
            workspace=workspace)


@app.command()
def set(
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        setting_key: str = typer.Argument(
            None
            , help="The name of the configuration setting."
        ),
        setting_value: str = typer.Argument(
            None
            , help="The value of the configuration setting."
        )
):
    """
    Set any specific configuration settings. 
    """
    config_settings = Config.OPTION_DEFAULTS
    if setting_key in config_settings:
        log.info(f'Updating local configuration {setting_key} setting for {workspace} workspace.')
        setting_dict = {setting_key: setting_value}
        Config().set_workspace_config(
            config_file=config_file,
            setting=setting_dict,
            workspace=workspace)
    else:
        raise typer.BadParameter(
            message=f"No configuration setting named {setting_key} available to modify. "
                    f"Try one of the following: {str.join(', ', config_settings)}"
        )


@app.command()
def get(
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        setting_key: str = typer.Argument(
            None
            , help="The name of the configuration setting."
        )
):
    """
    Get any specific configuration settings. 
    """
    config_settings = Config.OPTION_DEFAULTS
    if setting_key in config_settings:
        setting_value = Config().get_workspace_config(
            config_file=config_file,
            setting=setting_key,
            workspace=workspace)

        table = Table()
        table.add_column("Workspace", justify="right", style="cyan", no_wrap=True)
        table.add_column("Key", style="magenta")
        table.add_column("Value", justify="right", style="green")
        table.add_row(workspace, setting_key, str(setting_value))
        print(table)
    else:
        raise typer.BadParameter(
            message=f"No configuration setting named {setting_key} available to retrieve. "
                    f"Try one of the following: {str.join(', ', config_settings)}"
        )


@app.command()
def list(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file
):
    """
    List all configured workspaces. 
    """
    # Load and parse the configuration file
    config = Config.load_config(config_file)

    # Load and parse the credentials file
    auth = ApiAuth.find_and_parse_user_credentials(bigeye_conf)

    """
    Format credential and config files into table that looks like the following:
    Workspace Name |    ID  |   Credential Type
    --------------      --      ---------------
    DEFAULT             123     Browser     
    data-science        234     Basic
    """
    table = Table()
    table.add_column("Workspace", justify="right", style="cyan", no_wrap=True)
    table.add_column("ID", style="magenta")
    table.add_column("Credential Type", justify="right", style="green")
    for key, value in config.items():
        cred_type = None
        if auth.get(section=key, option='browser', fallback=None):
            cred_type = 'Browser'
        elif auth.get(section=key, option='user', fallback=None):
            cred_type = 'Basic'
        elif auth.get(section=key, option='api_key', fallback=None):
            cred_type = 'Api Key'
        else:
            cred_type = 'Default'
        table.add_row(key, value.get('workspace_id'), cred_type)

    print(table)
