import logging
import os
import sys
from time import strftime, localtime

from typing import Tuple, Union

import rich
from rich import print
from rich.table import Table
from rich.progress import track

from bigeye_cli.functions import cli_client_factory
from bigeye_cli import global_options
from bigeye_sdk.controller.delta_controller import DeltaController
from bigeye_sdk.controller.lineage_controller import LineageController
from bigeye_sdk.functions.delta_functions import infer_column_mappings, build_ccm
from bigeye_sdk.functions.table_functions import fully_qualified_table_to_elements
from bigeye_sdk.generated.com.bigeye.models.generated import (
    Delta,
    IdAndDisplayName,
    CreateComparisonTableRequest,
    ComparisonTableConfiguration,
)
from bigeye_sdk.model.delta_facade import (
    SimpleDeltaConfigurationFile,
    SimpleDeltaConfiguration,
    SimpleTargetTableComparison,
)

from typing import Optional, List

import typer

from bigeye_cli.model.cicd_conf import SimpleDeltaCicdConfigFile
from bigeye_sdk.log import get_logger
from bigeye_cli.model.vendor_report import VendorReport
from bigeye_sdk.model.enums import MatchType
from bigeye_sdk.model.protobuf_message_facade import (
    SimpleColumnMapping,
    SimpleNamedSchedule,
)

log = get_logger(__file__)

app = typer.Typer(no_args_is_help=True, help="Deltas Commands for Bigeye CLI")


@app.command()
def suggest_deltas(
    bigeye_conf: str = global_options.bigeye_conf,
    config_file: str = global_options.config_file,
    workspace: str = global_options.workspace,
    source_selector: str = typer.Option(
        ...,
        "--source_selector",
        "-source",
        help="The pattern of tables in the source to select. Wildcard (*) indicates all tables or all "
        "schemas, e.g. source_1.*.* would be all schemas in source_1.",
    ),
    target_selector: List[str] = typer.Option(
        ...,
        "--target_selector",
        "-target",
        help="The pattern of tables in the target to select. Wildcard (*) indicates all tables or all "
        "schemas, e.g. source_2.*.* would be all schemas in source_2.",
    ),
    match_type: Optional[MatchType] = typer.Option(
        MatchType.STRICT,
        "--match_type",
        "-mt",
        help="How to match tables between the source and target destinations. Strict will only create relations "
        "if table names match exactly, Fuzzy will attempt to create relations using a fuzzy match.",
        case_sensitive=False,
    ),
    output_path: str = typer.Option(
        ...,
        "--output_path",
        "-op",
        help="File to write the delta configuration.",
    ),
):
    """Suggests and creates Deltas with default behavior and outputs all Simple Delta Configurations to a file."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)
    lineage_controller = LineageController(client)
    delta_controller = DeltaController(client)

    upstream_tables = lineage_controller.get_tables_from_selector(
        selector=source_selector
    )

    target_1_tables = lineage_controller.get_tables_from_selector(
        selector=target_selector[0]
    )
    matching_targets_indexed_by_target_1_name = {}

    if len(target_selector) > 2:
        sys.exit("Specify 1 target table for a standard delta or 2 for n-way delta.")

    if len(target_selector) == 2:
        target_2_tables = lineage_controller.get_tables_from_selector(
            target_selector[1]
        )
        matching_target_tables = lineage_controller.infer_relationships_from_lists(
            target_1_tables, target_2_tables
        )
        matching_targets_indexed_by_target_1_name = {
            mtt[0].name: mtt[1] for mtt in matching_target_tables
        }

    matching_tables = lineage_controller.infer_relationships_from_lists(
        upstream=upstream_tables, downstream=target_1_tables, match_type=match_type
    )

    log.info(
        f"Identified {len(matching_tables)} table relationships between source and target selectors."
    )

    count_successful_suggestions = 0
    configs = []
    logging.disable(level=logging.INFO)
    for match in track(matching_tables, description="Generating suggestions..."):
        source = match[0]
        target_1 = match[1]
        target_2 = matching_targets_indexed_by_target_1_name.get(target_1.name, None)
        target = [target_1, target_2] if target_2 else [target_1]
        try:
            configs.append(
                delta_controller.create_template_delta_config(source, target)
            )
            count_successful_suggestions += 1
        except Exception as e:
            log.warning(
                f"Failed to create delta template for source table: {source.name}"
            )

    logging.disable(level=logging.NOTSET)

    template = SimpleDeltaConfigurationFile(
        type="DELTA_CONFIGURATION_FILE", deltas=[c.dict() for c in configs]
    )

    log.info(
        f"Successfully created {count_successful_suggestions} of {len(matching_tables)}"
        f" delta suggestions."
    )
    output = template.save(
        output_path=output_path, default_file_name=f"delta_suggestions"
    )
    typer.secho(
        f"\nDelta Suggestions file generated at: {output}\n", fg="green", bold=True
    )

    raise typer.Exit()


@app.command()
def create_delta(
    bigeye_conf: str = global_options.bigeye_conf,
    config_file: str = global_options.config_file,
    workspace: str = global_options.workspace,
    delta_conf_file: str = typer.Option(
        ..., "--delta_conf", "-dc", help="Simple Delta configuration file."
    ),
    update_lineage: bool = typer.Option(
        False,
        "--update_lineage",
        "-ul",
        help="Should lineage between source and target be checked/created if doesn't exist.",
    ),
):
    """Creates deltas between tables from a Simple Delta configuration file that contains multiple delta configurations.
    Enforces 1:1 column comparisons by case-insensitive column names if no column mappings are declared in
    configuration."""

    client = cli_client_factory(bigeye_conf, config_file, workspace)
    sdc = SimpleDeltaConfigurationFile.load(delta_conf_file)
    deltas = client.create_deltas_from_simple_conf(sdcl=sdc.deltas)

    if update_lineage:
        lineage_controller = LineageController(client=client)
        lineage_controller.create_relations_from_deltas(deltas)

    raise typer.Exit()


@app.command()
def run_delta(
    bigeye_conf: str = global_options.bigeye_conf,
    config_file: str = global_options.config_file,
    workspace: str = global_options.workspace,
    delta_id: int = typer.Option(..., "--delta_id", "-did", help="Id of delta."),
    await_results: bool = typer.Option(
        False,
        "--await_results",
        "-ar",
        help="Should command wait for delta run to complete, default False.",
    ),
):
    """Runs a delta by Delta ID."""
    print("Running a Delta now ... ")
    client = cli_client_factory(bigeye_conf, config_file, workspace)
    delta = client.run_a_delta(delta_id=delta_id, await_results=await_results)

    if await_results:
        log.info(f"Delta run completed")
        table = rich.table.Table()
        table.add_column(
            f"{delta.name} \nrun at {strftime('%Y-%m-%d %H:%M:%S', localtime(delta.last_run_at_epoch_seconds))}",
            justify="right",
            style="cyan",
            width=50,
        )
        table.add_column(justify="right", style="green")
        table.add_row("Total Metrics", str(delta.total_metric_count))
        table.add_row(
            "Healthy Metrics",
            str(
                delta.total_metric_count
                - delta.failed_metric_count
                - delta.alerting_metric_count
            ),
        )
        table.add_row("Alerting Metrics", str(delta.alerting_metric_count))
        table.add_row("Failed Metrics", str(delta.failed_metric_count))
        print(table)


@app.command()
def create_template(
    bigeye_conf: str = global_options.bigeye_conf,
    config_file: str = global_options.config_file,
    workspace: str = global_options.workspace,
    fully_qualified_source_name: str = typer.Option(
        ...,
        "--source_table_name",
        "-stn",
        help="The fully qualified name of the source table",
    ),
    fully_qualified_target_name: List[str] = typer.Option(
        ...,
        "--target_table_name",
        "-ttn",
        help="The fully qualified name of the target table",
    ),
    output_path: str = typer.Option(
        ...,
        "--output_path",
        "-op",
        help="Path to write the template.",
    ),
):
    """Create a template delta configuration file based on table names."""
    if len(fully_qualified_target_name) > 2:
        sys.exit("Specify 1 target table for a standard delta or 2 for n-way delta.")

    client = cli_client_factory(bigeye_conf, config_file, workspace)

    swh, fq_source_schema, source_table = fully_qualified_table_to_elements(
        fully_qualified_source_name
    )
    source = client.get_tables(
        schema=[fq_source_schema], table_name=[source_table]
    ).tables[0]

    source_metrics_types = client.get_delta_applicable_metric_types(
        table_id=source.id
    ).metric_types

    comparisons = []

    for tn in fully_qualified_target_name:
        twh, fq_target_schema, target_table = fully_qualified_table_to_elements(tn)
        target = client.get_tables(
            schema=[fq_target_schema], table_name=[target_table]
        ).tables[0]
        target_metric_types = client.get_delta_applicable_metric_types(
            table_id=target.id
        ).metric_types
        column_mappings = infer_column_mappings(
            source_metric_types=source_metrics_types,
            target_metric_types=target_metric_types,
        )
        simple_mappings = [
            SimpleColumnMapping.from_datawatch_object(obj=cm) for cm in column_mappings
        ]

        comparisons.append(
            SimpleTargetTableComparison(
                fq_target_table_name=tn,
                delta_column_mapping=simple_mappings,
                source_filters=[],
                target_filters=[],
                group_bys=[],
            ).dict()
        )

    configuration = SimpleDeltaConfiguration(
        delta_name=f"{fully_qualified_source_name} <> {fully_qualified_target_name}",
        fq_source_table_name=fully_qualified_source_name,
        target_table_comparisons=comparisons,
        tolerance=0.0,
        notification_channels=[],
        cron_schedule=SimpleNamedSchedule(
            name="Enter schedule name",
            cron="Define cron, if schedule does not exist. Otherwise just specify name.",
        ),
    )

    template = SimpleDeltaConfigurationFile(
        type="DELTA_CONFIGURATION_FILE", deltas=[configuration]
    )

    template.save(output_path=output_path, default_file_name="delta_template")
    typer.echo(f"File written at {output_path}delta_template.yml")

    raise typer.Exit()


@app.command()
def cicd(
    bigeye_conf: str = global_options.bigeye_conf,
    config_file: str = global_options.config_file,
    workspace: str = global_options.workspace,
    delta_cicd_config: str = typer.Option(
        ...,
        "--delta_cicd_config",
        "-dcc",
        help="The yaml file containing the parameters for the DeltaCICDConfig class",
    ),
):
    """Creates a delta based on SimpleDeltaConfiguration and integrates the results with the provided VCS vendor."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    delta_cicd = SimpleDeltaCicdConfigFile.load(file_name=delta_cicd_config).cicd_conf
    vendor_report: VendorReport = delta_cicd.report_type.value(
        github_token=os.environ["GITHUB_TOKEN"]
    )

    swh, fq_source_schema, source_table = fully_qualified_table_to_elements(
        delta_cicd.fq_source_table_name
    )
    twh, fq_target_schema, target_table = fully_qualified_table_to_elements(
        delta_cicd.fq_target_table_name
    )

    log.info("Beginning CICD delta process...")

    source = client.get_tables(
        schema=[fq_source_schema], table_name=[source_table]
    ).tables[0]
    target = client.get_tables(
        schema=[fq_target_schema], table_name=[target_table]
    ).tables[0]

    log.info("Looking for existing Delta with same name.")
    client.delete_deltas_by_name(delta_names=[delta_cicd.delta_name])
    if not delta_cicd.delta_column_mapping:
        source_metrics_types = client.get_delta_applicable_metric_types(
            table_id=source.id
        ).metric_types
        target_metric_types = client.get_delta_applicable_metric_types(
            table_id=target.id
        ).metric_types
        column_mappings = infer_column_mappings(
            source_metric_types=source_metrics_types,
            target_metric_types=target_metric_types,
        )
    else:
        column_mappings = [
            build_ccm(scm=cm, source_table=source, target_table=target) for cm in delta_cicd.delta_column_mapping
        ]


    comparisons = [
        ComparisonTableConfiguration(name=delta_cicd.delta_name,
                                     source_table_id=source.id,
                                     target_table_id=target.id,
                                     column_mappings=column_mappings)
    ]

    delta = Delta(
        name=delta_cicd.delta_name,
        source_table=IdAndDisplayName(id=source.id, display_name=source.name),
        comparison_table_configurations=comparisons,
        notification_channels=[
                    nc.to_datawatch_object() for nc in delta_cicd.notification_channels
                ]
    )

    response = client.upsert_delta(delta=delta)
    delta_run = client.run_a_delta(delta_id=response.delta.id, await_results=True)

    delta_info = client.get_delta_info(delta_id=delta_run.id)

    base_url = f"{client.get_base_url()}/w/{client.config.workspace_id}/deltas"
    exit_code = vendor_report.publish(
            base_url, delta_cicd.fq_source_table_name, delta_cicd.fq_target_table_name, delta_info
    )

    if exit_code != 0 and delta_cicd.group_bys:
        log.info("Alerts detected. Running new delta with specified groups.")
        group_by_columns = delta_cicd.group_bys[0].source_column_name
        group_by_name = f"{delta_cicd.delta_name} -- GROUPED BY {group_by_columns}"
        client.delete_deltas_by_name(delta_names=[group_by_name])
        group_bys = [gbc.to_datawatch_object() for gbc in delta_cicd.group_bys]
        gb_compare = comparisons[0]
        gb_compare.group_bys = group_bys
        delta.name = group_by_name
        delta.comparison_table_configurations = [gb_compare]


        gb_response = client.upsert_delta(delta=delta)
        gb_delta_run = client.run_a_delta(delta_id=gb_response.delta.id, await_results=True)
        delta_gb_run = client.get_delta_info(
            delta_id=gb_delta_run.id
        )

        if delta_gb_run.delta.alerting_metric_count != 0 or delta_gb_run.delta.failed_metric_count != 0:
            vendor_report.publish_group_bys(
                base_url,
                delta_cicd.fq_source_table_name,
                delta_cicd.fq_target_table_name,
                delta_gb_run,
            )

    sys.exit(exit_code)
