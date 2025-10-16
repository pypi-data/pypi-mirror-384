from typing import Optional

import typer

import bigeye_cli.__version__ as bigeye_cli_version
import bigeye_sdk.__version__ as bigeye_sdk_version

from bigeye_cli.functions import print_markdown
from bigeye_sdk.authentication.config import Config, WorkspaceConfig
from bigeye_sdk.functions.version import check_package_for_updates
from bigeye_sdk.log import get_logger

from bigeye_cli import CLI_DOCS_MD
from bigeye_cli.bigconfig import bigconfig_commands
from bigeye_cli.workspace import workspace_commands
from bigeye_cli.deltas import deltas_commands
from bigeye_cli.lineage import lineage_commands
from bigeye_cli.catalog import catalog_commands
from bigeye_cli.metric import metric_commands
from bigeye_cli.issues import issue_commands
from bigeye_cli.collections import collection_commands
from bigeye_cli.configure import configure_commands

# create logger
log = get_logger(__file__)

app = typer.Typer(no_args_is_help=True,
                  pretty_exceptions_show_locals=False,
                  pretty_exceptions_short=True,
                  help="""Bigeye CLI""")
app.add_typer(catalog_commands.app, name='catalog')
app.add_typer(metric_commands.app, name='metric')
app.add_typer(deltas_commands.app, name='deltas')
app.add_typer(workspace_commands.app, name='workspace')
app.add_typer(issue_commands.app, name='issues')
app.add_typer(bigconfig_commands.app, name='bigconfig')
app.add_typer(collection_commands.app, name='collections')
app.add_typer(lineage_commands.app, name='lineage')
app.add_typer(configure_commands.app, name='configure')


def _check_cli_and_sdk_versions(config_file: str, workspace: str):
    try:
        config = Config.load_config(config_file)
        workspace_config = WorkspaceConfig(**config[workspace])
        check_package_for_updates(
            pypi_package_name='bigeye-cli',
            internal_package_name='Bigeye CLI',
            installed_version=bigeye_cli_version.version,
            auto_update_enabled=workspace_config.auto_update_enabled,
            warning_message_disabled=workspace_config.disable_auto_update_message
        )

        check_package_for_updates(
            pypi_package_name='bigeye-sdk',
            internal_package_name='Bigeye SDK',
            installed_version=bigeye_sdk_version.version,
            auto_update_enabled=workspace_config.auto_update_enabled,
            warning_message_disabled=workspace_config.disable_auto_update_message
        )
    except:
        pass


@app.callback(invoke_without_command=True)
def options_callback(
        version: Optional[bool] = typer.Option(
            None, "--version", help="Bigeye CLI and SDK Versions"),
        readme: Optional[bool] = typer.Option(
            None, "--readme", help="Prints Readme."),
        verbose: Optional[bool] = typer.Option(
            None, "--verbose", help="Enables full output."),
        config_file: str = typer.Option(
            None, "--config_file", "-c",
            help="Bigeye CLI Configuration File Path", envvar='BIGEYE_API_CONFIG_FILE'),
        workspace: str = typer.Option(
            'DEFAULT', "--workspace", "-w",
            help="Name of the workspace configuration.", envvar='BIGEYE_WORKSPACE')
):
    _check_cli_and_sdk_versions(config_file, workspace)

    if version:
        typer.echo(f'Bigeye CLI Version: {bigeye_cli_version.version}\n'
                   f'Bigeye SDK Version: {bigeye_sdk_version.version}')
        raise typer.Exit()
    elif readme:
        print_markdown(file=CLI_DOCS_MD)
    elif verbose:
        app.pretty_exceptions_show_locals = True
        app.add_typer(typer_instance=app)

        
@app.command(deprecated=True)
def credential():
    raise typer.BadParameter('The bigeye credential command has been deprecated. Please use bigeye configure. '
                             'Instructions for usage can be found at https://docs.bigeye.com/docs/cli.')



if __name__ == '__main__':
    app()
