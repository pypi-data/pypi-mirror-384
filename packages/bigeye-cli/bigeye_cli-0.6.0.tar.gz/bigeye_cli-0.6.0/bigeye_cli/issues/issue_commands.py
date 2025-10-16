from typing import Optional, List

import typer

from bigeye_cli import global_options
from bigeye_cli.functions import cli_client_factory, write_issue_info
from bigeye_sdk.log import get_logger

log = get_logger(__file__)

app = typer.Typer(no_args_is_help=True, help='Issues Commands for Bigeye CLI')

"""
File should contain commands that impact issues.
"""


@app.command()
def get_issues(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        warehouse_ids: Optional[List[int]] = typer.Option(
            None
            , "--warehouse_id"
            , "-wid"
            , help="Warehouse IDs."),
        schemas: Optional[List[str]] = typer.Option(
            None
            , "--schema_name"
            , "-sn"
            , help="Schema names"),
        metric_ids: Optional[List[int]] = typer.Option(
            None
            , "--metric_id"
            , "-mid"
            , help="Metric IDs."
        ),
        collection_ids: Optional[List[int]] = typer.Option(
            None
            , "--collection_id"
            , "-cid"
            , help="Collection IDs"),
        issue_ids: Optional[List[int]] = typer.Option(
            None
            , "--issue_id"
            , "-iid"
            , help="Issue IDs"),
        output_path: str = typer.Option(
            ...
            , "--output_path"
            , "-op"
            , help="File to write the failed metric configurations to.")
):
    """Gets issues and writes info to files."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    issues = client.get_issues(warehouse_ids=warehouse_ids,
                               schema_names=schemas,
                               metric_ids=metric_ids,
                               collection_ids=collection_ids,
                               issue_ids=issue_ids)

    write_issue_info(output_path=output_path, issues=issues)


@app.command()
def update_issue(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        issue_id: int = typer.Option(
            ...
            , "--issue_id"
            , "-iid"
            , help="Issue ID"),
        issue_status: str = typer.Option(
            None
            , "--issue_status"
            , "-status"
            , help="The status update. Options are ACKNOWLEDGED or CLOSED."),
        updated_by: str = typer.Option(
            None
            , "--updated_by"
            , "-by"
            , help="The user providing the update."),
        message: str = typer.Option(
            None
            , "--message"
            , "-m"
            , help="The message to attach to the issue."),
        closing_label: str = typer.Option(
            None
            , "--closing_label"
            , "-cl"
            , help="Used to train Bigeye when closing an issue. Options are TRUE_POSITIVE, FALSE_POSITIVE, EXPECTED.")
):
    """Updates an issue in Bigeye and returns the Issue object from the protobuff."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    client.update_issue(issue_id=issue_id,
                        issue_status=issue_status,
                        updated_by=updated_by,
                        update_message=message,
                        closing_label=closing_label)
