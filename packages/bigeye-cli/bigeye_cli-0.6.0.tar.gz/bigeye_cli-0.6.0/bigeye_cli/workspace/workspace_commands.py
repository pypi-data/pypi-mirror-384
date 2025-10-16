import json
from typing import List, Optional
import typer
import yaml

from bigeye_cli import global_options
from bigeye_cli.exceptions.exceptions import ResourceNotFoundException
from bigeye_cli.functions import cli_client_factory, write_named_schedules

from bigeye_sdk.log import get_logger
from bigeye_sdk.client.enum import Method
from bigeye_sdk.functions.core_py_functs import int_enum_enum_list_joined
from bigeye_sdk.generated.com.bigeye.models.generated import (
    TimeIntervalType,
    MetricConfiguration,
    TimeInterval,
    IdAndDisplayName,
    GroupUserOperation,
    BulkChangeGroupUsersResponse,
    Workspace,
    Group,
    RoleOperation,
    Group, BulkChangeGroupGrantsResponse,
)

log = get_logger(__file__)

app = typer.Typer(no_args_is_help=True, help="Workspace Commands for Bigeye CLI")

"""Commands that pertain to a Bigeye workspace"""


@app.command()
def unschedule_all_metrics(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
):
    """Unschedule all metrics in a workspace."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    wids: List[int] = [s.id for s in client.get_sources().sources]

    # Could do bulk change by wid and metric type which are necessary in the api call.
    mcs: List[dict] = [
        mil.metric_configuration.to_dict()
        for mil in client.get_metric_info_batch_post(warehouse_ids=wids).metrics
    ]

    mc = MetricConfiguration()
    ti = TimeInterval()
    ti.interval_type = TimeIntervalType.DAYS_TIME_INTERVAL_TYPE
    ti.interval_value = 0
    mc.schedule_frequency = ti

    log.info(mc.to_json())

    # TODO: this is an antipattern.  is there another way to set the value to 0?
    mc_dict = mc.to_dict()
    mc_dict["scheduleFrequency"]["intervalValue"] = 0

    log.info(json.dumps(mc_dict))

    url = "/api/v1/metrics/batch"

    response = client._call_datawatch(Method.PUT, url=url, body=json.dumps(mc))


@app.command()
def schedule_all_metrics(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        time_interval_type: int = typer.Option(
            TimeIntervalType.HOURS_TIME_INTERVAL_TYPE.value,
            "--time_interval_type",
            "-type",
            help=f"Time interval type.\n {int_enum_enum_list_joined(enum=TimeIntervalType)}",
        ),
        interval_value: int = typer.Option(
            ...,
            "--interval_value",
            "-value",
            help="Number of intervals to set on all metric schedules.  If 0 use unschedule all metrics.",
        ),
):
    """Schedule all metrics in a workspace."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    tit = TimeIntervalType(time_interval_type)

    wids: List[int] = [s.id for s in client.get_sources().sources]

    # Could do bulk change by wid and metric type which are necessary in the api call.
    mcs: List[dict] = [
        mil.metric_configuration.to_dict()
        for mil in client.get_metric_info_batch_post(warehouse_ids=wids).metrics
    ]

    for mc in mcs:
        mc["scheduleFrequency"] = {
            "intervalType": tit.name,
            "intervalValue": interval_value,
        }

        url = "/api/v1/metrics"

        response = client._call_datawatch(Method.POST, url=url, body=json.dumps(mc))


@app.command()
def create_named_schedule(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        name: str = typer.Option(
            ..., "--name", "-sn", help="The user defined name of the schedule"
        ),
        cron: str = typer.Option(
            ..., "--cron", "-c", help="The cron string to define the schedule"
        ),
):
    """Create a named, cron based schedule"""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    response = client.create_named_schedule(name=name, cron=cron)
    log.info(
        f"Named schedule created\n\tname: {response.name}\n\tcron:{response.cron}\n\tid:{response.id}"
    )


@app.command()
def upsert_named_schedule(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        name: Optional[str] = typer.Option(
            None, "--name", "-sn", help="The user defined name of the schedule"
        ),
        cron: Optional[str] = typer.Option(
            None, "--cron", "-c", help="The cron string to define the schedule"
        ),
        schedule_file: Optional[str] = typer.Option(
            None, "--schedule_file", "-sf", help="A yaml file containing a schedule definition."
        )
):
    """Create a named, cron based schedule. Files have priority over arguments"""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if schedule_file:
        with open(schedule_file) as fin:
            named_schedule = yaml.safe_load(stream=fin)
            name = named_schedule["schedule_name"]
            cron = named_schedule["cron"]

    response = client.get_named_schedule()
    named_schedule = [s for s in response.named_schedules if s.name.lower() == name.lower()]
    if named_schedule:
        schedule_id = named_schedule[0].id
        response = client.create_named_schedule(id=schedule_id, name=name, cron=cron)
    else:
        response = client.create_named_schedule(name=name, cron=cron)

    log.info(
        f"Named schedule upsert\n\tname: {response.name}\n\tcron: {response.cron}\n\tid: {response.id}"
    )


@app.command()
def delete_named_schedule(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        name: str = typer.Option(
            ..., "--name", "-sn", help="The user defined name of the schedule"
        ),
):
    """Delete a named schedule."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)
    response = client.get_named_schedule()
    named_schedules = [s for s in response.named_schedules if s.name.lower() == name.lower()]

    try:
        schedule = named_schedules[0]
        client.delete_named_schedule(schedule_id=schedule.id)
    except IndexError:
        raise ResourceNotFoundException(f"Schedule '{name}' was not found in workspace {client.config.workspace_id}")


@app.command()
def export_named_schedule(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        names: List[str] = typer.Option(
            [], "--name", "-sn", help="The name of the schedule(s) to export. None means all"
        ),
        output_path: Optional[str] = typer.Option(
            None, "--output_path", "-op", help="Path to output files. None means current directory"
        )
):
    """Export cron schedule to yaml file"""
    client = cli_client_factory(bigeye_conf, config_file, workspace)
    schedules = client.get_named_schedule().named_schedules

    if names:
        names = [sn.lower() for sn in names]
        schedules = [schedule for schedule in schedules if schedule.name.lower() in names]

    write_named_schedules(schedules=schedules, output_path=output_path)


@app.command()
def invite_user(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        user_name: str = typer.Option(..., "--user_name", "-name", help="User name."),
        email: str = typer.Option(
            ..., "--user_email", "-email", help="Email where invite will be sent."
        ),
        group_names: Optional[List[str]] = typer.Option(
            None,
            "--group_name",
            "-group",
            help="The names of the groups that the user should belong to. E.g. -group team1 -group team2",
        ),
):
    """Invite a user to a workspace."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if group_names is None:
        response = client.invite_user(
            user_name=user_name, user_email=email, group_ids=[]
        )
    else:
        group_names: List[str] = [g.lower() for g in group_names]
        grps: List[IdAndDisplayName] = [
            IdAndDisplayName(id=g.id, display_name=g.name)
            for g in client.get_groups().groups
            if g.name.lower() in group_names
        ]

        valid_group_names = [g.display_name.lower() for g in grps]
        for g in group_names:
            if g not in valid_group_names:
                log.info(
                    f"Group name `{g}` could not be found and will not be added to {user_name} user access."
                )

        response = client.invite_user(
            user_name=user_name, user_email=email, group_ids=[g.id for g in grps]
        )

    log.info(
        f"New user invited\n\tname: {response.name}\n\temail:{response.email}\n\tid:{response.id}"
    )


@app.command()
def edit_user(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        user_name: str = typer.Option(None, "--user_name", "-name", help="User name."),
        email: str = typer.Option(None, "--user_email", "-email", help="User email."),
        group_names: List[str] = typer.Option(
            ...,
            "--group_name",
            "-group",
            help="The names of the groups that should be edited for this users access. E.g. -group team1 -group team2",
        ),
        operation: int = typer.Option(
            GroupUserOperation.GROUP_USER_OPERATION_ADD.value,
            "--operation",
            "-op",
            help=f"Operation type.\n {int_enum_enum_list_joined(enum=GroupUserOperation)}",
        ),
):
    """Edit an existing user's access to groups."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if email:
        user = next(filter(lambda u: u.email == email, client.get_users().users), None)
    elif user_name:
        user = next(
            filter(lambda u: u.name == user_name, client.get_users().users), None
        )
    else:
        raise typer.BadParameter(
            f"Expected either `--user_name` or `--user_email` to be provided."
        )

    if user is None:
        raise typer.BadParameter(
            f"No user can be found with values provided. Please double check values and try again."
        )

    group_names: List[str] = [g.lower() for g in group_names]
    grps: List[IdAndDisplayName] = [
        IdAndDisplayName(id=g.id, display_name=g.name)
        for g in client.get_groups().groups
        if g.name.lower() in group_names
    ]

    valid_group_names = [g.display_name.lower() for g in grps]
    for g in group_names:
        if g not in valid_group_names:
            log.warning(
                f"Group name `{g}` could not be found and will not be added to {user_name} user access."
            )

    response: BulkChangeGroupUsersResponse = client.edit_users_groups(
        user_ids=[user.id],
        group_ids=[g.id for g in grps],
        operation=GroupUserOperation(operation),
    )

    # warn user that some user/group pairs may have failed to update
    for failed_update in response.failed_updates:
        failed_group = next(
            filter(lambda g: g.id == failed_update.group_id, grps), None
        )
        log.warning(
            f"User group pair failed to be updated. User = {user.name}, Group = {failed_group.display_name}"
        )

    # validate all successful updates
    for succeeded_group in response.successful_ids:
        succeeded_group = next(
            filter(lambda g: g.id == succeeded_group.group_id, grps), None
        )
        log.info(
            f"User {user.name} has been updated for the {succeeded_group.display_name} group."
        )


@app.command()
def delete_user(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        user_name: str = typer.Option(None, "--user_name", "-name", help="User name."),
        email: str = typer.Option(None, "--user_email", "-email", help="User email."),
):
    """Deletes a users account."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if email:
        user = next(filter(lambda u: u.email == email, client.get_users().users), None)
    elif user_name:
        user = next(
            filter(lambda u: u.name == user_name, client.get_users().users), None
        )
    else:
        raise typer.BadParameter(
            f"Expected either `--user_name` or `--user_email` to be provided."
        )

    if user is None:
        raise typer.BadParameter(
            f"No user can be found with options provided. Please double check and try again."
        )

    client.delete_user(user.id)
    log.info(f"User {user.name} has been deleted.")


@app.command()
def upsert_workspace(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        workspace_name: str = typer.Option(
            ..., "--workspace_name", "-name", help="Workspace name."
        ),
        workspace_id: int = typer.Option(
            None, "--workspace_id", "-id", help="Workspace ID."
        ),
):
    """Create or update a workspace."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if workspace_id:
        response = client.update_workspace(workspace_name, workspace_id)
    else:
        workspace: Workspace = next(
            filter(
                lambda w: w.name.lower() == workspace_name.lower(),
                client.get_workspaces().workspaces,
            ),
            None,
        )
        if workspace:
            response = client.update_workspace(workspace_name, workspace.id)
        else:
            response = client.create_workspace(workspace_name)

    log.info(f"Workspace created\n\tname: {response.name}\n\tid: {response.id}")


@app.command()
def delete_workspace(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        workspace_name: str = typer.Option(
            ..., "--workspace_name", "-name", help="Workspace name."
        ),
):
    """Delete a workspace."""
    from rich.prompt import Confirm
    from rich.text import Text

    client = cli_client_factory(bigeye_conf, config_file, workspace)

    workspace: Workspace = next(
        filter(
            lambda w: w.name.lower() == workspace_name.lower(),
            client.get_workspaces().workspaces,
        ),
        None,
    )

    if not workspace:
        raise typer.BadParameter(f"No workspace named {workspace_name} can be found.")

    confirmed = Confirm.ask(
        Text(
            f"This workspace has {len(workspace.sources)} sources. "
            f"Are you sure you want to delete workspace {workspace.name}? This cannot be undone.",
            style="bold green",
        )
    )

    if confirmed:
        client.delete_workspace(workspace.id)
        log.info(f"Workspace {workspace.name} has been deleted.")
    else:
        log.info(f"Request has been cancelled.")


@app.command()
def upsert_group(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        group_name: str = typer.Option(..., "--group_name", "-name", help="Group name."),
        group_id: int = typer.Option(None, "--group_id", "-id", help="Group ID."),
):
    """Create or update a group."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if group_id:
        response = client.update_group(group_name, group_id)
    else:
        group: Group = next(
            filter(
                lambda g: g.name.lower() == group_name.lower(),
                client.get_groups().groups,
            ),
            None,
        )
        if group:
            response = client.update_group(group_name, group.id)
        else:
            response = client.create_group(group_name)

    log.info(f"Group created\n\tname: {response.name}\n\tid: {response.id}")


@app.command()
def edit_group_access(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        group_name: str = typer.Option(..., "--group-name", "-name", help="Group name."),
        group_id: int = typer.Option(None, "--group-id", "-id", help="Group ID."),
        workspace_names: List[str] = typer.Option(
            ...,
            "--workspace-name",
            "-wn",
            help="List of workspace names to edit access. E.g. -wn workspace1 -wn workspace2",
        ),
        access_level: str = typer.Option(
            "Edit",
            "--access-level",
            "-access",
            help="The access this group should have to the workspaces provided. Must be `View`, `Edit`, or `Manage`",
        ),
        operation: int = typer.Option(
            RoleOperation.ROLE_OPERATION_GRANT.value,
            "--operation",
            "-op",
            help=f"Operation type.\n {int_enum_enum_list_joined(enum=RoleOperation)}",
        ),
):
    """Edit the workspaces that a group can access."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if access_level.lower() not in ["view", "edit", "manage"]:
        raise typer.BadParameter(
            f"Invalid access level provided. Must be `View`, `Edit`, or `Manage`"
        )

    if group_id:
        group: Group = next(
            filter(
                lambda g: g.name.lower() == group_name.lower(),
                client.get_groups().groups,
            ),
            None,
        )
    elif group_name:
        group: Group = next(
            filter(
                lambda g: g.name.lower() == group_name.lower(),
                client.get_groups().groups,
            ),
            None,
        )
    else:
        raise typer.BadParameter(
            f"Expected either `--group-id` or `--group-name` to be provided."
        )

    if not group:
        raise typer.BadParameter(f"No group named {group_name} can be found.")

    workspaces: List[Workspace] = [
        w for w in client.get_workspaces().workspaces if w.name in workspace_names
    ]
    role = next(r for r in client.get_roles().roles
                if r.name.lower() == access_level.lower())
    workspace_ids = [w.id for w in workspaces]

    # warn user of workspace names not found
    valid_workspace_names = [w.name.lower() for w in workspaces]
    for w in workspace_names:
        if w.lower() not in valid_workspace_names:
            log.warning(
                f"Workspace name `{w}` could not be found and will not be added to {group_name} access."
            )

    response: BulkChangeGroupGrantsResponse = client.edit_group_roles(
        group=group,
        role=role,
        workspace_ids=workspace_ids,
        operation=RoleOperation(operation),
    )

    # warn user that some group/role pairs may have failed to update
    for failed_update in response.failed_updates:
        log.warning(
            f"Group role failed to be updated. Group = {failed_update.request.group.display_name}, "
            f"Role = {failed_update.request.role.name}, "
            f"Workspace = {failed_update.request.workspace.display_name}"
        )

    # validate all successful updates
    for successful_update in response.successful_requests:
        log.info(
            f"Group {successful_update.group.display_name} has been updated for the {successful_update.role.name} role "
            f"in the {successful_update.workspace.display_name} workspace."
        )


@app.command()
def delete_group(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        group_name: str = typer.Option(..., "--group_name", "-name", help="Group name."),
):
    """Delete a group."""
    from rich.prompt import Confirm
    from rich.text import Text

    client = cli_client_factory(bigeye_conf, config_file, workspace)

    group: Group = next(
        filter(
            lambda g: g.name.lower() == group_name.lower(), client.get_groups().groups
        ),
        None,
    )

    if not group:
        raise typer.BadParameter(f"No group named {group_name} can be found.")

    confirmed = Confirm.ask(
        Text(
            f"This group has {len(group.users)} users. "
            f"Are you sure you want to delete group {group.name}? This cannot be undone.",
            style="bold green",
        )
    )

    if confirmed:
        client.delete_group(group.id)
        log.info(f"Group {group.name} has been deleted.")
    else:
        log.info(f"Request has been cancelled.")
