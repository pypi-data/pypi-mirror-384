# create logger
import warnings
from os import listdir
from os.path import join, isfile
from typing import List, Dict

import smart_open
import typer
import json
from pathlib import Path

import yaml

from bigeye_cli import global_options
from bigeye_cli.enums import MetricFileType
from bigeye_sdk.controller.metric_controller import MetricController
from bigeye_sdk.functions.metric_functions import get_file_name_for_metric
from bigeye_sdk.functions.bigconfig_functions import build_fq_name
from bigeye_sdk.model.dbt_schema import (
    SimpleDbtSchema,
    relationships_test_names,
    relationships_template,
)
from bigeye_sdk.model.protobuf_enum_facade import (
    MetricStatus,
    SimpleLookbackType,
    SimpleFieldType,
)

from bigeye_sdk.log import get_logger
from bigeye_cli.functions import (
    write_metric_info,
    cli_client_factory,
    write_debug_queries,
)
from bigeye_sdk.generated.com.bigeye.models.generated import (
    MetricInfoList,
    MetricInfo,
    TableList,
    Table,
    MetricConfiguration,
)
from bigeye_sdk.model.big_config import BigConfig, TagDeployment, ColumnSelector
from bigeye_sdk.model.metric_facade import SimpleUpsertMetricRequest
from bigeye_sdk.model.protobuf_message_facade import (
    SimpleAutoThreshold,
    SimpleLookback,
    SimpleMetricDefinition,
    SimpleCollection,
)

log = get_logger(__file__)

app = typer.Typer(no_args_is_help=True, help="Metric Commands for Bigeye CLI")

"""
File should contain commands that impact metrics by id or ids.
"""


@app.command()
def run(
    bigeye_conf: str = global_options.bigeye_conf,
    config_file: str = global_options.config_file,
    workspace: str = global_options.workspace,
    metric_ids: List[int] = typer.Option(
        ..., "--metric_id", "-mid", help="Metric Ids."
    ),
    queue: bool = typer.Option(
        False,
        "--queue",
        "-q",
        help="Submit the batch to a queue. (Recommended for larger batches)",
    ),
):
    """Run metric by id(s)"""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    client.batch_run_metrics(metric_ids=metric_ids, queue=queue)


@app.command()
def get_info(
    bigeye_conf: str = global_options.bigeye_conf,
    config_file: str = global_options.config_file,
    workspace: str = global_options.workspace,
    metric_ids: List[int] = typer.Option(
        ..., "--metric_id", "-mid", help="Metric Ids."
    ),
    metric_status: MetricStatus = typer.Option(
        None,
        "--metric_status",
        "-ms",
        help="Used to query metric of particular status.",
    ),
    output_path: str = typer.Option(
        ...,
        "--output_path",
        "-op",
        help="File to write the failed metric configurations to.",
    ),
    only_metric_conf: bool = typer.Option(
        False, "--conf_only", help="Output only the metric configuration."
    ),
):
    """Outputs metric info to a file.  Includes metric configuration and details about recent runs."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if metric_status:
        metric_status_name = metric_status.name
    else:
        metric_status_name = None

    mil: MetricInfoList = client.get_metric_info_batch_post(
        metric_ids=metric_ids, status=metric_status_name
    )

    write_metric_info(
        output_path=output_path, metrics=mil, only_metric_conf=only_metric_conf
    )


@app.command()
def upsert_from_path(
    bigeye_conf: str = global_options.bigeye_conf,
    config_file: str = global_options.config_file,
    workspace: str = global_options.workspace,
    target_warehouse_id: int = typer.Option(
        ...,
        "--target_warehouse_id",
        "-twid",
        help="Deploy Metrics to target Warehouse ID.",
    ),
    source_path: str = typer.Option(
        ...,
        "--source_path",
        "-sp",
        help="Source path file containing the metrics to migrate.",
    ),
    set_row_creation_time: bool = typer.Option(
        False,
        "--set_row_creation_time",
        "-srct",
        help="Set the row creation time in target warehouse for tables found in source path.",
    ),
    update_collections: bool = typer.Option(
        False,
        "--update_collections",
        "-uc",
        help="Update existing collections to include new metrics from target warehouse.",
    ),
):
    """Upsert multiple metrics from files stored in path."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    all_files = [
        join(source_path, f)
        for f in listdir(source_path)
        if isfile(join(source_path, f)) and ".json" in f
    ]

    def open_metric_info(file) -> MetricInfo:
        with smart_open.open(file) as fin:
            return MetricInfo().from_json(fin.read())

    mil: MetricInfoList = MetricInfoList()
    mil.metrics = [open_metric_info(f) for f in all_files]

    table_names = {m.metric_metadata.dataset_name for m in mil.metrics}
    schema_names = {m.metric_metadata.schema_name for m in mil.metrics}

    tables: List[Table] = client.get_tables(
        warehouse_id=[target_warehouse_id],
        schema=list(schema_names),
        table_name=list(table_names),
    ).tables

    t_ix: Dict[str, Table] = {t.name: t for t in tables}

    if set_row_creation_time:
        warnings.warn(
            "set_row_creation_time is deprecated and will be removed in a future version. "
            "Row creation time is managed in the metricConfiguration with the 'rctOverride' field.",
            DeprecationWarning
        )

    for m in mil.metrics:
        mc = m.metric_configuration

        log.info(mc)

        try:
            rmc = client.upsert_metric(
                schedule_frequency=mc.schedule_frequency,
                filters=mc.filters,
                group_bys=mc.group_bys,
                thresholds=mc.thresholds,
                notification_channels=mc.notification_channels,
                warehouse_id=target_warehouse_id,
                dataset_id=t_ix[m.metric_metadata.dataset_name].id,
                metric_type=mc.metric_type,
                parameters=mc.parameters,
                lookback=mc.lookback,
                lookback_type=mc.lookback_type,
                metric_creation_state=mc.metric_creation_state,
                grain_seconds=mc.grain_seconds,
                muted_until_epoch_seconds=mc.muted_until_epoch_seconds,
                name=mc.name,
                description=mc.description,
                rct_override=mc.rct_override
            )

            if update_collections:
                for c in m.collections:
                    client.upsert_metric_to_collection(
                        collection_id=c.id, add_metric_ids=[rmc.id]
                    )

        except Exception as e:
            log.exception(f"Error for file: {get_file_name_for_metric(m)}")
            log.exception(e)


@app.command()
def upsert(
    bigeye_conf: str = global_options.bigeye_conf,
    config_file: str = global_options.config_file,
    workspace: str = global_options.workspace,
    file: str = typer.Option(
        ...,
        "--file",
        "-f",
        help="File containing SimpleUpsedrtMetricRequest or MetricConfiguration",
    ),
    file_type: MetricFileType = typer.Option(
        ...,
        "--file_type",
        "-t",
        help="Metric File Type.  Simple conforms to SimpleUpsertMetricRequest and Full conforms to "
        "MetricConfiguration",
    ),
    target_warehouse_id: int = typer.Option(
        None,
        "--warehouse_id",
        "-wid",
        help="(Optional) Warehouse ID.  If specified it will reduce the text based search for the table."
        "warehouse",
    ),
    existing_metric_id: int = typer.Option(
        None,
        "--metric_id",
        "-mid",
        help="(Optional) Metric Id.  If specified it will reduce the text based search for existing metric.",
    ),
):
    """Upsert single metric from file."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if file_type == MetricFileType.SIMPLE:
        with open(file, "r") as file:
            simple_metric_conf = yaml.safe_load(file.read())

        simple_request = SimpleUpsertMetricRequest(**simple_metric_conf)

        client.upsert_metric_from_simple_template(
            sumr=simple_request, existing_metric_id=existing_metric_id
        )

    elif file_type == MetricFileType.FULL:
        with open(file, "r") as file:
            mcf = yaml.safe_load(file.read())

        mc = MetricConfiguration().from_dict(mcf)

        client.upsert_metric(metric_configuration=mc)


@app.command()
def get_metric_queries(
    bigeye_conf: str = global_options.bigeye_conf,
    config_file: str = global_options.config_file,
    workspace: str = global_options.workspace,
    metric_ids: List[int] = typer.Option(
        ..., "--metric_id", "-mid", help="Metric Ids."
    ),
    output_path: str = typer.Option(
        ...,
        "--output_path",
        "-op",
        help="File to write the failed metric configurations to.",
    ),
):
    """Gets the debug queries for all metrics by warehouse id, schema names, or table ids."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    r = client.get_debug_queries(metric_ids=metric_ids)

    write_debug_queries(output_path=output_path, queries=r)


@app.command()
def dbt_tests_to_metrics(
    bigeye_conf: str = global_options.bigeye_conf,
    config_file: str = global_options.config_file,
    workspace: str = global_options.workspace,
    warehouse_name: str = typer.Option(
        ..., "--warehouse_name", "-wn", help="The name of the source to deploy metrics"
    ),
    schema_name: str = typer.Option(
        ..., "--schema_name", "-sn", help="The name of the schema to deploy metrics"
    ),
    schema_file: str = typer.Option(
        ..., "--schema_file", "-sf", help="The path to the dbt schema file"
    ),
    use_autothresholds: bool = typer.Option(
        False, "--use_auto", "-auto", help="Use autothresholds over default constant"
    ),
    to_bigconfig: bool = typer.Option(
        False,
        "--to_bigconfig",
        "-bigconfig",
        help="Convert the dbt tests to bigconfig.",
    ),
    output_path: str = typer.Option(
        Path.cwd(),
        "--output_path",
        "-op",
        help="Output path where bigconfig file will be saved. If no output path is defined "
        "then current working directory will be used. Requires --to_bigconfig to be true.",
    ),
):
    """Convert tests in a dbt schema.yml to metrics in Bigeye"""
    with open(schema_file) as fin:
        schema_yml = yaml.safe_load(fin)
    dbt_schema = SimpleDbtSchema(**schema_yml)
    client = cli_client_factory(bigeye_conf, config_file, workspace)
    metric_controller = MetricController(client=client)
    source = client.get_sources_by_name(source_names=[warehouse_name])[warehouse_name]
    dbt_tables: Dict[str, List[SimpleMetricDefinition]] = {
        t.name: t.column_tests for t in dbt_schema.models
    }
    tables: Dict[str, Table] = {
        t.name.lower(): t
        for t in client.get_tables(
            warehouse_id=[source.id], schema=[schema_name]
        ).tables
        if t.name.lower() in dbt_tables.keys()
    }

    default_lookback_type: bool = [
        ac.boolean_value
        for ac in client.get_advanced_configs()
        if ac.key == "metric.data_time_window.default"
    ][0]
    default_lookback = (
        SimpleLookback()
        if default_lookback_type
        else SimpleLookback(lookback_type=SimpleLookbackType.DATA_TIME)
    )

    tag_deployments: List[TagDeployment] = []
    for t, tests in dbt_tables.items():
        try:
            bigeye_table = tables[t]
        except KeyError:
            log.error(
                f"Table {t} was not found in {source.name}.{schema_name}. Check that Bigeye has access to the "
                f"dataset."
            )
            continue

        column_selectors: List[str] = []
        for test in tests:
            # Multiple tests per column, but only want 1 column ref to be passed into bigconfig export
            test_column = build_fq_name(
                source.name, schema_name, t, test.parameters[0].column_name
            )
            if test_column not in column_selectors:
                tag_deployments.append(
                    TagDeployment(
                        column_selectors=[ColumnSelector(name=test_column)],
                        metrics=tests,
                    )
                )
                column_selectors.append(test_column)

            if use_autothresholds:
                test.threshold = SimpleAutoThreshold(type="AUTO")

            if bigeye_table.metric_time_column:
                test.lookback = default_lookback

                try:
                    if test.metric_name == "dbt_test_relationships":
                        templates = [
                            t
                            for t in client.get_all_metric_templates()
                            if t.source.name.lower() == warehouse_name.lower()
                            and t.name.lower() in relationships_test_names
                        ]
                        if not templates:
                            log.info(
                                f"No template found in source {warehouse_name} with names: {relationships_test_names}"
                            )
                            log.info(
                                f"Creating template '{relationships_test_names[0]}' in source {warehouse_name}"
                            )
                            template = client.upsert_metric_template(
                                id=0,
                                name=relationships_test_names[0],
                                template=relationships_template,
                                return_type=SimpleFieldType.BOOLEAN,
                                parameters=[
                                    "column_to_check=COLUMN_REFERENCE",
                                    "lookup_column=STRING",
                                    "lookup_table=STRING",
                                ],
                                source=source,
                            ).metric_template
                        else:
                            template = templates[0]

                        test.metric_type.template_id = template.id
                        test.metric_type.template_name = template.name
                        for p in test.parameters:
                            if p.key == "lookup_table":
                                sdb = schema_name.split(".")
                                p.string_value = (
                                    f'"{sdb[0]}"."{p.string_value}"'
                                    if len(sdb) == 1
                                    else f'"{sdb[0]}"."{sdb[1]}"."{p.string_value}"'
                                )
                except Exception as e:
                    log.error(f"Error handling relationships test for dbt with {e}")
                    log.info("Moving to next test.")
                    continue

                mc = test.to_datawatch_object(to_config=True)
                mc.warehouse_id = source.id
                mc.dataset_id = bigeye_table.id

                # Create metrics if not outputting to bigconfig
                if not to_bigconfig:
                    log.info(
                        f"Creating metric {test.metric_name} for table {source.name}.{schema_name}.{t}"
                    )
                    client.upsert_metric(metric_configuration=mc)

    if to_bigconfig:
        collection: SimpleCollection = SimpleCollection(
            name="DBT Tests", description="Monitoring results of dbt tests."
        )
        bigconfig = BigConfig.tag_deployments_to_bigconfig(
            tag_deployments=tag_deployments, collection=collection
        )
        file_name = collection.name.lower().replace(" ", "_")
        output = bigconfig.save(
            output_path=output_path,
            default_file_name=f"{file_name}.bigconfig",
            custom_formatter=bigconfig.format_bigconfig_export,
        )
        typer.secho(
            f"\nSample bigconfig file generated at: {output}\n", fg="green", bold=True
        )
