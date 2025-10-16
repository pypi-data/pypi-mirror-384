import json
import logging
import os
import sys
import time

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

import typer
import yaml

from rich.progress import track

from bigeye_cli.exceptions.exceptions import MissingArgumentException
from bigeye_sdk.client.enum import Method

from bigeye_cli import global_options
from bigeye_sdk.functions.dbt import parse_dbt_manifest
from bigeye_sdk.functions.file_functs import read_json_file
from bigeye_sdk.functions.notifications import (
    send_email,
    post_slack_snippet,
    post_webhook_request,
)
from bigeye_sdk.functions.search_and_match_functions import fuzzy_match
from bigeye_sdk.model.dbt_manifest import DbtManifest
from bigeye_sdk.model.protobuf_enum_facade import (
    MetricStatus,
    SimpleMetricCategory,
    SimpleMetricTemplateFieldType,
    SimpleSchemaChangeOperation
)
from bigeye_sdk.functions.aws import get_secret
from bigeye_sdk.generated.com.bigeye.models.generated import (
    MetricInfoList,
    WarehouseType,
    CreateSourceRequest,
    TimeIntervalType,
    PredefinedMetricName,
    MetricConfiguration,
    ForecastModelType,
    Source,
    Table,
    User,
    OwnableType,
    SchemaChange,
)
from bigeye_sdk.log import get_logger
from bigeye_cli.functions import (
    write_metric_info,
    cli_client_factory,
    write_table_info,
    write_debug_queries,
    write_metric_templates, write_yaml_templates, write_virtual_tables,
)
from bigeye_sdk.functions.metric_functions import has_auto_threshold
from bigeye_sdk.functions.core_py_functs import int_enum_enum_list_joined
from bigeye_sdk.model.schema_change import SourceSchemaChange

# create logger
log = get_logger(__file__)

app = typer.Typer(no_args_is_help=True, help="Catalog Commands for Bigeye CLI")

"""
File should contain commands that will impact catalog, table, or schema level changes to a Bigeye workspace.  This
would include metrics batched at any of these levels.
"""


@app.command()
def regen_autometrics(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        warehouse_id: int = typer.Option(
            None,
            "--warehouse_id",
            "-wid",
            help="Warehouse ID.  If none will look for Table IDs.  If value then will pull all table ids for "
                 "warehouse",
        ),
        schema_names: Optional[List[str]] = typer.Option(
            None,
            "--schema_name",
            "-sn",
            help="List of Schema Names  E.g. -sn schema_1 -sn schema_2.  Do not include warehouse name -- "
                 "GREENE_HOMES_DEMO_STANDARD.CONFORMED is fully qualified and CONFORMED is the schema name.",
        ),
        table_ids: Optional[List[int]] = typer.Option(
            None, "--table_id", "-tid", help="List of Table IDs.  E.g. -tid 123 -tid 124"
        ),
):
    """Regenerates Autometrics by warehouse id OR warehouse id and list of schema names OR list of table ids."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if not table_ids:
        table_ids = client.get_table_ids(
            warehouse_id=[warehouse_id], schemas=schema_names
        )

    if table_ids:
        log.info(f"Regenerating autometrics on: {table_ids}")
        for tid in table_ids:
            client.regen_autometrics(table_id=tid)
    else:
        raise Exception(
            "Could not identify table_ids to run.  Provide either a valid list of table ids OR a valid "
            "warehouse ID OR a valid warehouse ID and list of valid schema names"
        )


@app.command()
def delete_metrics(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        warehouse_id: int = typer.Option(
            None, "--warehouse_id", "-wid", help="Warehouse ID"
        ),
        schema_names: Optional[List[str]] = typer.Option(
            None,
            "--schema_name",
            "-sn",
            help="List of Schema Names.  E.g. -sn schema_1 -sn schema_2.",
        ),
        table_ids: Optional[List[int]] = typer.Option(
            None, "--table_id", "-tid", help="Table IDs.  E.g. -tid 123 -tid 124"
        ),
        metric_type: Optional[List[str]] = typer.Option(
            None,
            "--metric_type",
            "-m",
            help=f"Delete by name of the metric type."
                 f"{', '.join([i.name for i in PredefinedMetricName])}",
        ),
):
    """Delete metrics in a warehouse id, by schema names, or by table_ids.  Also, can filter by multipe
    metric types."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    mil: MetricInfoList = client.get_metric_info_batch_post(
        warehouse_ids=[warehouse_id], table_ids=table_ids
    )

    if schema_names:
        mil.metrics = [
            m for m in mil.metrics if m.metric_metadata.schema_name in schema_names
        ]

    if metric_type:
        mil.metrics = [
            m
            for m in mil.metrics
            if SimpleMetricCategory.get_metric_name(m.metric_configuration.metric_type)
               in metric_type
        ]

    metrics = [m.metric_configuration for m in mil.metrics]

    client.delete_metrics(metrics=metrics)


@app.command()
def rebuild(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        warehouse_id: int = typer.Option(
            ..., "--warehouse_id", "-wid", help="Warehouse ID"
        ),
        schema_name: str = typer.Option(None, "--schema_name", "-sn", help="Schema Name"),
):
    """Rebuilds/Reprofiles a source by warehouse id or a schema by warehouse id and schema name."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    log.info(
        f"Rebuilding Catalog Resource.  Warehouse ID: {warehouse_id}  Schema Name: {schema_name}"
    )
    client.rebuild(warehouse_id=warehouse_id, schema_name=schema_name)


@app.command()
def get_table_info(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        warehouse_id: int = typer.Option(
            None, "--warehouse_id", "-wid", help="Warehouse ID"
        ),
        schema_names: Optional[List[str]] = typer.Option(
            None,
            "--schema_name",
            "-sn",
            help="List of Schema Names.  E.g. -sn schema_1 -sn schema_2.",
        ),
        table_ids: Optional[List[int]] = typer.Option(
            None, "--table_id", "-tid", help="Table IDs. E.g. -tid 123 -tid 124"
        ),
        table_names: Optional[List[str]] = typer.Option(
            None,
            "--table_name",
            "-tn",
            help="Table Namess. E.g. -tn some_table -tn some_other_table",
        ),
        output_path: str = typer.Option(
            ...,
            "--output_path",
            "-op",
            help="File to write the failed metric configurations to.",
        ),
):
    """Outputs table info to a file for an entire warehouse, certain schemas, or certain tables."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    wids = [] if not warehouse_id else [warehouse_id]

    tables = client.get_tables(
        warehouse_id=wids, schema=schema_names, ids=table_ids, table_name=table_names
    )

    write_table_info(output_path=output_path, tables=tables.tables)


@app.command()
def get_metric_info(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        warehouse_id: int = typer.Option(
            None, "--warehouse_id", "-wid", help="Warehouse ID"
        ),
        schema_names: Optional[List[str]] = typer.Option(
            None,
            "--schema_name",
            "-sn",
            help="List of Schema Names.  E.g. -sn schema_1 -sn schema_2.",
        ),
        table_ids: Optional[List[int]] = typer.Option(
            None,
            "--table_id",
            "-tid",
            help="Table IDs. E.g. -tid 123 -tid 124" "or schema names.",
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
        warehouse_ids=[warehouse_id], table_ids=table_ids, status=metric_status_name
    )

    if schema_names:
        mil.metrics = [
            m for m in mil.metrics if m.metric_metadata.schema_name in schema_names
        ]

    write_metric_info(
        output_path=output_path, metrics=mil, only_metric_conf=only_metric_conf
    )


@app.command()
def run_metrics(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        warehouse_id: int = typer.Option(
            None, "--warehouse_id", "-wid", help="Warehouse ID"
        ),
        schema_names: Optional[List[str]] = typer.Option(
            None,
            "--schema_name",
            "-sn",
            help="List of Schema Names.  E.g. -sn schema_1 -sn schema_2.",
        ),
        table_ids: Optional[List[int]] = typer.Option(
            None, "--table_id", "-tid", help="Table IDs. E.g. -tid 123 -tid 124"
        ),
        table_names: Optional[List[str]] = typer.Option(
            None,
            "--table_name",
            "-tn",
            help="Table Names. E.g. -tn some_table -tn some_other_table",
        ),
        queue: bool = typer.Option(
            False,
            "--queue",
            "-q",
            help="Submit the batch to a queue. (Recommended for larger batches)",
        ),
):
    """Runs all metrics for a warehouse, particular schemas in a warehouse, or tables by id."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    wids = [] if not warehouse_id else [warehouse_id]

    mil = client.get_metric_info_batch_post(warehouse_ids=wids, table_ids=table_ids)

    if schema_names and table_names:
        mids = [
            m.metric_configuration.id
            for m in mil.metrics
            if m.metric_metadata.schema_name in schema_names
               and m.metric_metadata.dataset_name in table_names
        ]
    elif schema_names:
        mids = [
            m.metric_configuration.id
            for m in mil.metrics
            if m.metric_metadata.schema_name in schema_names
        ]
    elif table_names:
        mids = [
            m.metric_configuration.id
            for m in mil.metrics
            if m.metric_metadata.dataset_name in table_names
        ]
    else:
        mids = [m.metric_configuration.id for m in mil.metrics]

    client.batch_run_metrics(metric_ids=mids, queue=queue)


@app.command()
def add_source(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        secret_name: str = typer.Option(
            None,
            "--secret_name",
            "-sn",
            help="""The name of the secret to retrieve from AWS Secrets Manager""",
        ),
        secret_region_name: str = typer.Option(
            "us-west-2",
            "--secret_region_name",
            "-srn",
            help="AWS Secret Manager Region Name",
        ),
        source_catalog_config_file: str = typer.Option(
            None,
            "--source_catalog_config_file",
            "-sccf",
            help="The file containing the necessary parameters for adding a source to Bigeye.",
        ),
):
    """Adds a source to specified Bigeye workspace.  Supports either source configs stored in AWS Secrets manager OR
    locally in file."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if secret_name:
        secret = get_secret(secret_name, secret_region_name)
        source_config = yaml.safe_load(secret["SecretString"])
    else:
        log.info(f"Loading source config file: {source_catalog_config_file}")
        with open(source_catalog_config_file) as fin:
            source_config = yaml.safe_load(fin)

    db_type = source_config["database_type"].upper()
    source_config["database_type"] = WarehouseType[f"DATABASE_TYPE_{db_type}"]

    client.create_source(CreateSourceRequest(**source_config))


@app.command()
def delete_source(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        warehouse_id: int = typer.Option(
            None, "--warehouse_id", "-wid", help="""The ID of the warehouse to delete."""
        ),
):
    """Delete a source from specified Bigeye workspace."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    client.delete_source(warehouse_id)


@app.command()
def backfill_autothresholds(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        warehouse_id: int = typer.Option(
            None, "--warehouse_id", "-wid", help="Warehouse ID"
        ),
        schema_names: Optional[List[str]] = typer.Option(
            None,
            "--schema_name",
            "-sn",
            help="List of Schema Names.  E.g. -sn schema_1 -sn schema_2.",
        ),
        table_ids: Optional[List[int]] = typer.Option(
            None, "--table_id", "-tid", help="Table IDs.  E.g. -tid 123 -tid 124"
        ),
):
    """Backfills autothresholds by warehouse id, schema names, and/or table ids."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    mil: MetricInfoList = client.get_metric_info_batch_post(
        warehouse_ids=[warehouse_id], table_ids=table_ids
    )
    if schema_names:
        mil.metrics = [
            m for m in mil.metrics if m.metric_metadata.schema_name in schema_names
        ]

    mids = [
        m.metric_configuration.id
        for m in mil.metrics
        if has_auto_threshold(m.metric_configuration.thresholds)
    ]

    client.backfill_autothresholds(metric_ids=mids)


@app.command()
def backfill_metrics(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        warehouse_id: int = typer.Option(
            None, "--warehouse_id", "-wid", help="Warehouse ID"
        ),
        schema_names: Optional[List[str]] = typer.Option(
            None,
            "--schema_name",
            "-sn",
            help="List of Schema Names.  E.g. -sn schema_1 -sn schema_2.",
        ),
        table_ids: Optional[List[int]] = typer.Option(
            None, "--table_id", "-tid", help="Table IDs.  E.g. -tid 123 -tid 124"
        ),
        delete_history: Optional[bool] = typer.Option(
            None, "--delete_history", help="Delete metric run history"
        ),
        queue: bool = typer.Option(
            False,
            "--queue",
            "-q",
            help="Submit the batch to a queue. (Recommended for larger batches)",
        ),
):
    """Backfills metrics by warehouse id, schema names, and/or table ids."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    mil: MetricInfoList = client.get_metric_info_batch_post(
        warehouse_ids=[warehouse_id], table_ids=table_ids
    )
    if schema_names:
        mil.metrics = [
            m for m in mil.metrics if m.metric_metadata.schema_name in schema_names
        ]

    metadata_metric_mids = [
        m.metric_configuration.id
        for m in mil.metrics
        if m.metric_configuration.metric_type
    ]

    mids = [m.metric_configuration.id for m in mil.metrics]

    for mid in mids:
        try:
            client.backfill_metric(metric_ids=[mid], delete_history=delete_history)
        except Exception as e:
            log.exception(e)
    client.batch_run_metrics(metric_ids=mids, queue=queue)


@app.command()
def run_metrics(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        warehouse_id: int = typer.Option(
            None, "--warehouse_id", "-wid", help="Warehouse ID"
        ),
        schema_names: Optional[List[str]] = typer.Option(
            None,
            "--schema_name",
            "-sn",
            help="List of Schema Names.  E.g. -sn schema_1 -sn schema_2.",
        ),
        table_ids: Optional[List[int]] = typer.Option(
            None, "--table_id", "-tid", help="Table IDs.  E.g. -tid 123 -tid 124"
        ),
        queue: bool = typer.Option(
            False,
            "--queue",
            "-q",
            help="Submit the batch to a queue. (Recommended for larger batches)",
        ),
):
    """Runs metrics by warehouse id, schema names, and/or table ids"""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    mil: MetricInfoList = client.get_metric_info_batch_post(
        warehouse_ids=[warehouse_id], table_ids=table_ids
    )
    if schema_names:
        mil.metrics = [
            m for m in mil.metrics if m.metric_metadata.schema_name in schema_names
        ]

    metadata_metric_mids = [
        m.metric_configuration.id
        for m in mil.metrics
        if m.metric_configuration.metric_type
    ]

    mids = [m.metric_configuration.id for m in mil.metrics]

    client.batch_run_metrics(metric_ids=mids, queue=queue)


@app.command()
def schedule_all_metrics(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        warehouse_id: int = typer.Option(
            None, "--warehouse_id", "-wid", help="Warehouse ID"
        ),
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
    """Updates schedule for all metrics in a warehouse."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    tit = TimeIntervalType(time_interval_type)

    wids: List[int] = [warehouse_id]

    # Could do bulk change by wid and metric type which are necessary in the api call.
    mcs: List[MetricConfiguration] = [
        mil.metric_configuration
        for mil in client.get_metric_info_batch_post(warehouse_ids=wids).metrics
    ]

    for mc in mcs:
        body = mc.to_dict()
        body["scheduleFrequency"]["intervalType"] = tit.name
        body["scheduleFrequency"]["intervalValue"] = interval_value
        if "thresholds" in body:
            body.pop("thresholds")

        url = "/api/v1/metrics"

        response = client._call_datawatch(Method.POST, url=url, body=json.dumps(body))


@app.command()
def unschedule_all_metrics(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        warehouse_id: int = typer.Option(
            None, "--warehouse_id", "-wid", help="Warehouse ID"
        ),
        schema_name: Optional[str] = typer.Option(
            None, "--schema_name", "-sn", help="List of Schema Name.  E.g. -sn schema_1."
        ),
        table_ids: Optional[List[int]] = typer.Option(
            None, "--table_id", "-tid", help="Table IDs.  E.g. -tid 123 -tid 124"
        ),
):
    """Unschedule all metrics by warehouse, schema or tables."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    mcs: List[MetricConfiguration] = [
        mil.metric_configuration
        for mil in client.get_metric_info_batch_post(
            warehouse_ids=[warehouse_id], schema_name=schema_name, table_ids=table_ids
        ).metrics
    ]
    url = "/api/v1/metrics"

    for mc in mcs:
        body = mc.to_dict()
        body["scheduleFrequency"] = {
            "intervalType": TimeIntervalType.MINUTES_TIME_INTERVAL_TYPE,
            "intervalValue": 0,
        }
        if "thresholds" in body:
            for t in body["thresholds"]:
                if "autoThreshold" in t:
                    t["autoThreshold"][
                        "modelType"
                    ] = ForecastModelType.BOOTSTRAP_THRESHOLD_MODEL_TYPE

        response = client._call_datawatch(Method.POST, url=url, body=json.dumps(body))


@app.command()
def set_metric_time(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        warehouse_id: int = typer.Option(
            None, "--warehouse_id", "-wid", help="Warehouse ID"
        ),
        schema_id: Optional[int] = typer.Option(
            None, "--schema_id", "-sid", help="Schema ID"
        ),
        table_ids: Optional[List[int]] = typer.Option(
            None, "--table_id", "-tid", help="List of table IDs."
        ),
        metric_column_names: Optional[List[str]] = typer.Option(
            ..., "--metric_column_name", "-cn", help="Possible metric column names."
        ),
        replace_set_metric_times: bool = typer.Option(
            False,
            "--replace",
            "-r",
            help="replace metric times if already present on tables?  Default is false.",
        ),
):
    """Sets metric times from a list of possible metric column names.  Can set for whole warehouse or for a list of
    table IDs."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if warehouse_id and table_ids:
        raise Exception("Must include either table IDs OR warehouse ID OR schema ID.")
    elif warehouse_id or schema_id:
        client.set_source_metric_times(
            column_names=metric_column_names,
            wid=warehouse_id,
            sid=schema_id,
            replace=replace_set_metric_times,
        )
    elif table_ids:
        client.set_table_metric_times(
            column_names=metric_column_names,
            table_ids=table_ids,
            replace=replace_set_metric_times,
        )
    else:
        raise Exception("Must include either table IDs OR warehouse ID OR schema ID.")


@app.command()
def unset_metric_time(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        warehouse_id: int = typer.Option(
            None, "--warehouse_id", "-wid", help="Warehouse ID"
        ),
        table_ids: Optional[List[int]] = typer.Option(
            None, "--table_id", "-tid", help="List of table IDs."
        ),
):
    """Unsets metric times for whole warehouse or for a list og table IDs."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if warehouse_id and table_ids:
        raise Exception("Must include either table IDs OR warehouse id.")
    elif warehouse_id:
        client.unset_source_metric_times(wid=warehouse_id)
    elif table_ids:
        client.unset_table_metric_times(table_ids=table_ids)
    else:
        raise Exception("Must include either table IDs OR warehouse id.")


@app.command()
def get_metric_queries(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        warehouse_id: int = typer.Option(
            None, "--warehouse_id", "-wid", help="Warehouse ID"
        ),
        schema_names: Optional[List[str]] = typer.Option(
            None,
            "--schema_name",
            "-sn",
            help="List of Schema Names.  E.g. -sn schema_1 -sn schema_2.",
        ),
        table_ids: Optional[List[int]] = typer.Option(
            None, "--table_id", "-tid", help="Table IDs.  E.g. -tid 123 -tid 124"
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

    mil: MetricInfoList = client.get_metric_info_batch_post(
        warehouse_ids=[warehouse_id], table_ids=table_ids
    )
    if schema_names:
        mil.metrics = [
            m for m in mil.metrics if m.metric_metadata.schema_name in schema_names
        ]

    mids = [m.metric_configuration.id for m in mil.metrics]

    r = client.get_debug_queries(metric_ids=mids)

    write_debug_queries(output_path=output_path, queries=r)


@app.command()
def upsert_template(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        source_name: str = typer.Option(
            None,
            "--source_name",
            "-sn",
            help="The name of the source where the template will be defined",
        ),
        template_name: str = typer.Option(
            None, "--name", "-tn", help="The user defined name of the template"
        ),
        template_body: str = typer.Option(
            None, "--body", "-tb", help="The string to define the template"
        ),
        return_type: SimpleMetricTemplateFieldType = typer.Option(
            None,
            "--returns",
            "-rt",
            help="The data type returned by the template; i.e. NUMERIC, BOOLEAN",
        ),
        # TODO: Update to List[Tuple[str, SimpleMetricTemplateParameterType]] when supported by typer.
        parameters: List[str] = typer.Option(
            None,
            "--params",
            "-p",
            help="A list of key/value pairs for parameters; ex. -p column=COLUMN_REFERENCE -p table=STRING",
        ),
        template_file: Optional[str] = typer.Option(
            None,
            "--template_file",
            "-tf",
            help="A file containing a template definition.",
        )
):
    """Create or update a template for a source. Files have priority over arguments"""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if template_file:
        with open(template_file) as fin:
            template = yaml.safe_load(stream=fin)
        source_name = template["source_name"]
        template_name = template["name"]
        template_body = template["body"]
        return_type = template["return_type"]
        parameters = template["parameters"]

    source: Source = [s for s in client.get_sources().sources if s.name.lower() == source_name.lower()][
        0
    ]
    template = [t for t in client.get_all_metric_templates() if t.name.lower() == template_name.lower()]
    template_id = template[0].id if template else 0

    log.info(f"Creating metric template in warehouse {source.name}")

    r = client.upsert_metric_template(
        id=template_id,
        name=template_name,
        template=template_body,
        return_type=return_type,
        parameters=parameters,
        source=source,
    )
    log.info(
        f"Upsert for metric template complete:\n\tName: {r.metric_template.name}\n\t"
    )


@app.command()
def export_metric_template(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        names: List[str] = typer.Option(
            [], "--name", "-tn", help="The name of the template(s) to export. None means all"
        ),
        output_path: Optional[str] = typer.Option(
            None, "--output_path", "-op", help="Path to output files. None means current directory"
        )
):
    """Export metric templates to yaml files"""
    client = cli_client_factory(bigeye_conf, config_file, workspace)
    metric_templates = client.get_all_metric_templates()

    if names:
        names = [tn.lower() for tn in names]
        metric_templates = [template for template in metric_templates if template.name.lower() in names]

    write_yaml_templates(metric_templates=metric_templates, output_path=output_path)


@app.command()
def get_all_metric_templates(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        page_size: Optional[int] = typer.Option(
            0, "--page_size", "-ps", help="How many results to return per page"
        ),
        search: Optional[str] = typer.Option(
            "", "--search", "-s", help="A search string to narrow results"
        ),
        output_path: str = typer.Option(
            None, "--output_path", "-op", help="The path to output templates"
        ),
        file_name: Optional[str] = typer.Option(
            None, "--file_name", "-fn", help="User defined file name"
        ),
):
    """Retrieve all metric templates and output to a file."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)
    metric_templates = client.get_all_metric_templates(
        page_size=page_size, search=search
    )
    if not output_path:
        output_path = Path.cwd()

    write_metric_templates(
        output_path=output_path, metric_templates=metric_templates, file_name=file_name
    )


@app.command()
def delete_template(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        template_id: Optional[int] = typer.Option(
            None, "--template_id", "-tid", help="The ID of the metric template"
        ),
        template_name: Optional[str] = typer.Option(
            None, "--name", "-tn", help="The name of the metric template"
        )
):
    """Delete a template."""
    if not template_name and not template_id:
        raise MissingArgumentException("Template ID or name must be provided.")

    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if template_id:
        client.delete_metric_template(template_id=template_id)
        log.info(f"Template ID {template_id} deleted.")
    else:
        try:
            template_id = [
                t.id for t in client.get_all_metric_templates() if t.name.lower() == template_name.lower()
            ][0]
            client.delete_metric_template(template_id=template_id)
            log.info(f"Template {template_name} deleted.")
        except IndexError:
            log.info(f"No template found with the name {template_name}. Nothing to do.")


@app.command()
def upsert_virtual_table(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        virtual_table_name: Optional[str] = typer.Option(
            None, "--table_name", "-vtn", help="The name of the virtual table"
        ),
        sql: Optional[str] = typer.Option(None, "--sql", "-s", help="The SQL to define the table"),
        source_name: Optional[str] = typer.Option(
            None,
            "--source_name",
            "-sn",
            help="The name of the source where the virtual table will be defined",
        ),
        update: bool = typer.Option(
            False, "--update", "-u", help="Create if false. Update if true."
        ),
        table_file: Optional[str] = typer.Option(
            None,
            "--table_file",
            "-tf",
            help="A yaml file containing a template definition.",
        )
):
    """Create or update a virtual table. Files have priority over arguments"""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if table_file:
        with open(table_file) as fin:
            virtual_table = yaml.safe_load(stream=fin)
            source_name = virtual_table["source_name"]
            virtual_table_name = virtual_table["table_name"]
            sql = virtual_table["sql"]

    source: Source = [s for s in client.get_sources().sources if s.name == source_name][
        0
    ]

    if update:
        log.warning(
            f"The update flag has been deprecated. This command will now scan for virtual tables that match the"
            f"given source and virtual table names. If one is found, the virtual table will be updated, "
            f"else the virtual table will be created."
        )

    table: Table = next(
        (
            vt.table
            for vt in client.get_all_virtual_tables()
            if vt.table.warehouse_id == source.id
               and vt.table.name == virtual_table_name
        ),
        None,
    )

    if table:
        log.info(f"Update {table.name} in warehouse {source.name}")
        client.update_virtual_table(
            id=table.id, name=virtual_table_name, sql=sql, warehouse_id=source.id
        )
    else:
        log.info(
            f"Creating virtual table {virtual_table_name} in warehouse {source.name}"
        )
        client.create_virtual_table(
            name=virtual_table_name, sql=sql, warehouse_id=source.id
        )


@app.command()
def delete_virtual_table(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        virtual_table_name: str = typer.Option(
            ..., "--table_name", "-vtn", help="The name of the virtual table"
        ),
        source_name: str = typer.Option(
            ...,
            "--source_name",
            "-sn",
            help="The name of the source that contains the virtual table",
        ),
):
    """Delete a virtual table."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)
    source: Source = [s for s in client.get_sources().sources if s.name == source_name][
        0
    ]
    table: Table = [
        vt
        for vt in client.get_all_virtual_tables()
        if vt.table.warehouse_id == source.id and vt.table.name == virtual_table_name
    ][0].table

    client.delete_virtual_table(table_id=table.id)


@app.command()
def export_virtual_table(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        names: List[str] = typer.Option(
            [], "--name", "-vtn", help="The name of the virtual table(s) to export. None means all"
        ),
        output_path: Optional[str] = typer.Option(
            None, "--output_path", "-op", help="Path to output files. None means current directory"
        )
):
    """Export virtual table to yaml file"""
    client = cli_client_factory(bigeye_conf, config_file, workspace)
    virtual_tables = client.get_all_virtual_tables()

    if names:
        names = [vtn.lower() for vtn in names]
        virtual_tables = [vt for vt in virtual_tables if vt.table.name.lower() in names]

    write_virtual_tables(virtual_tables=virtual_tables, output_path=output_path)


@app.command()
def ingest_owners_from_dbt(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        dbt_manifest_file: Optional[str] = typer.Option(
            None, "--manifest_file", "-mf", help="The path to the dbt manifest file."
        ),
        source_name: Optional[str] = typer.Option(
            None,
            "--source_name",
            "-sn",
            help="The name of the source in Bigeye where owners will be ingested.",
        ),
        source_id: Optional[int] = typer.Option(
            None,
            "--source_id",
            "-sid",
            help="The id of the source in Bigeye where owners will be ingested.",
        ),
):
    """Ingest table owners from dbt manifest.json file."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    if not source_name and not source_id:
        raise typer.BadParameter(
            "Either the source ID or the source name is required for this command."
        )

    if not source_id:
        source_id = (
            client.get_sources_by_name(source_names=[source_name]).get(source_name).id
        )

    if not dbt_manifest_file:
        dbt_manifest_file = client.config.dbt_manifest_file or Path.cwd()

    manifest: DbtManifest = parse_dbt_manifest(dbt_manifest_file)
    users: List[User] = client.get_users().users
    users_by_name: Dict[str, User] = {u.name: u for u in users}
    users_by_email: Dict[str, User] = {u.email: u for u in users}
    tables = client.get_tables(warehouse_id=[source_id]).tables

    logging.disable(level=logging.INFO)
    for model_name, node in track(
            manifest.nodes.items(), description="Setting object owners..."
    ):
        matching_tables = [t for t in tables if t.name.lower() == node.name.lower()]

        if node.config.meta.owner and matching_tables:
            if users_by_name.get(node.config.meta.owner, None):
                for mt in matching_tables:
                    client.set_object_owner(
                        object_type=OwnableType.OWNABLE_TYPE_DATASET,
                        object_id=mt.id,
                        owner=users_by_name[node.config.meta.owner].id,
                    )
            elif users_by_email.get(node.config.meta.owner, None):
                for mt in matching_tables:
                    client.set_object_owner(
                        object_type=OwnableType.OWNABLE_TYPE_DATASET,
                        object_id=mt.id,
                        owner=users_by_email[node.config.meta.owner].id,
                    )
            else:
                cleaned_owner = node.config.meta.owner
                if node.config.meta.owner[0] == "@":
                    cleaned_owner = cleaned_owner[1:]
                cleaned_owner = cleaned_owner.split("@")[0].split("+")[0]
                fuzzy_name_matches = fuzzy_match(
                    search_string=cleaned_owner,
                    contents=[u.name for u in users],
                    min_match_score=25,
                )
                if fuzzy_name_matches:
                    first_fuzzy_match = fuzzy_name_matches[0]
                    for mt in matching_tables:
                        client.set_object_owner(
                            object_type=OwnableType.OWNABLE_TYPE_DATASET,
                            object_id=mt.id,
                            owner=users_by_name[first_fuzzy_match[1]].id,
                        )

                else:
                    log.warning(
                        f"No matching Bigeye user found for model: {model_name} - "
                        f"owner: {node.config.meta.owner}"
                    )


@app.command()
def ingest_dbt_core_run_info(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        target_path: Optional[str] = typer.Option(
            "./target",
            "--target_path",
            "-tp",
            help="The path to the target directory created with dbt run, build, and test commands.",
        ),
        project_name: Optional[str] = typer.Option(
            None,
            "--project_name",
            "-pn",
            help="The name of the dbt project. Will attempt to parse from metadata section of manifest.json, if not present",
        ),
        job_name: Optional[str] = typer.Option(
            None, "--job_name", "-jn", help="The name of the dbt job."
        ),
        job_run_id: Optional[str] = typer.Option(
            None, "--job_run_id", "-jid", help="The ID of the dbt job run."
        ),
        project_url: Optional[str] = typer.Option(
            None, "--project_url", "-purl", help="The URL of the project."
        ),
        job_url: Optional[str] = typer.Option(
            None, "--job_url", "-jurl", help="The URL of the job."
        ),
        job_run_url: Optional[str] = typer.Option(
            None, "--job_run_url", "-jrurl", help="The URL of the job run."
        ),
):
    """Ingest manifest.json and run_results.json from different dbt commands."""

    manifest_json = read_json_file(file_path=f"{target_path}/manifest.json")
    run_results_json = read_json_file(file_path=f"{target_path}/run_results.json")

    client = cli_client_factory(bigeye_conf, config_file, workspace)

    response = client.send_dbt_core_job_info(
        project_name=project_name,
        job_name=job_name,
        job_run_id=job_run_id,
        manifest_json=json.dumps(manifest_json),
        run_results_json=json.dumps(run_results_json),
        project_url=project_url,
        job_url=job_url,
        job_run_url=job_run_url,
    )

    log.info(
        f"The following response was returned:\n\n\t{response.to_json(indent=True)}"
    )


@app.command()
def track_schema_changes(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        source_names: List[str] = typer.Option(
            [],
            "--source",
            "-src",
            help="A list of source names to track. (None will track changes from all sources)",
        ),
        since: Optional[str] = typer.Option(
            "1970-01-01",
            "--since",
            "-s",
            help="Track schema changes from this date. (Formatted as yyyy-MM-dd)",
        ),
        frequency: Optional[int] = typer.Option(
            0,
            "--frequency",
            "-f",
            help="Every n hours to check for schema changes. (None will only run the check once)",
        ),
        change_types: List[SimpleSchemaChangeOperation] = typer.Option(
            [
                SimpleSchemaChangeOperation.DELETED,
                SimpleSchemaChangeOperation.CREATED,
                SimpleSchemaChangeOperation.TYPE_CHANGED,
            ],
            "--change_type",
            "-ct",
            help="The types of changes to track; i.e additions, changes, deletions. (None will track all types)",
        ),
        notification_channels: List[str] = typer.Option(
            [],
            "--channel",
            "-nc",
            help="A list of notification channels; e.g. -nc email@mydomain.com -nc #slack_channel -nc https://www.webhook.com",
        ),
        smtp_server: Optional[str] = typer.Option(
            None, "--server", "-smtp", help="The server to send emails."
        ),
        smtp_port: Optional[int] = typer.Option(
            587, "--port", "-p", help="The server port to send emails."
        ),
        slack_token: Optional[str] = typer.Option(
            None,
            "--token",
            "-t",
            help="The token to utilize the Slack web client. (Will attempt to use environment variable SLACK_BOT_TOKEN, if not set)",
        ),
):
    """Track schema changes for sources on demand or every n hour(s) and notify specified channels.
    Environment variables SMTP_USER and SMTP_PASSWORD MUST be set if using email notification.
    """

    hour_as_secs = 3600
    no_reply_at_bigeye = "noreply@bigeye.com"

    try:
        date_epoch = datetime.strptime(since, "%Y-%m-%d").timestamp()
    except ValueError as e:
        log.error(
            f"Error converting date {since}. Please ensure it formatted as yyyy-MM-dd."
        )
        log.info("The process will exit.")
        raise e

    emails = []
    slack_channels = []
    webhooks = []
    for nc in notification_channels:
        if "@" in nc:
            emails.append(nc)
        elif nc.startswith("#"):
            slack_channels.append(nc)
        elif nc.startswith("http"):
            webhooks.append(nc)
        else:
            log.error(f"Unrecognized notification channel: {nc}")
            log.warning(f"Schema changes will not be sent to {nc}")

    if emails:
        if not smtp_server:
            raise MissingArgumentException(
                "Email listed as notification channel but no email server specified to send one."
            )
        if not os.environ.get("SMTP_USER", None):
            raise MissingArgumentException(
                "Email listed as notification channel but no value set for environment variable SMTP_USER."
            )
        if not os.environ.get("SMTP_PASSWORD", None):
            raise MissingArgumentException(
                "Email listed as notification channel but no value set for environment variable SMTP_PASSWORD."
            )

    if slack_channels:
        if not slack_token and not os.environ.get("SLACK_BOT_TOKEN", None):
            raise MissingArgumentException(
                "Slack listed as notification channel but no value set for slack token or environment variable SLACK_BOT_TOKEN."
            )
        if not slack_token:
            slack_token = os.environ.get("SLACK_BOT_TOKEN")

    change_types = [ct.to_datawatch_object() for ct in change_types]

    client = cli_client_factory(bigeye_conf, config_file, workspace)

    sources = client.get_sources_by_name(source_names=source_names)
    while True:
        changes_by_source: Dict[str, List[SchemaChange]] = {}
        for s in sources.values():

            changes = []
            since_time = datetime.fromtimestamp(timestamp=date_epoch).strftime(
                "%m/%d/%Y, %H:%M"
            )
            log.info(f"Retrieving changes for source {s.name} since {since_time}")
            changes.extend(
                [
                    c
                    for c in client.fetch_schema_changes(source_id=s.id, page_size=1000)
                    if c.change_type in change_types and c.detected_at >= date_epoch
                ]
            )
            if changes:
                changes_by_source[s.name] = changes
            else:
                continue

        source_changes = [
            SourceSchemaChange(name=k, changes=v) for k, v in changes_by_source.items()
        ]

        all_alerts = ""
        alert_webhook = {}

        if source_changes:

            for change in source_changes:
                all_alerts += f"<br><br>{change.format_message()}</br></br>"
                alert_webhook.update(change.format_webhook())

            if emails:
                send_email(
                    server_name=smtp_server,
                    port=smtp_port,
                    user_name=os.environ.get("SMTP_USER"),
                    password=os.environ.get("SMTP_PASSWORD"),
                    sender=no_reply_at_bigeye,
                    subject=f"Schema changes detected in Bigeye since {since_time}",
                    recipient=emails,
                    body=all_alerts,
                )

            if slack_channels:
                post_slack_snippet(
                    slack_token=slack_token,
                    slack_channel=slack_channels,
                    body=alert_webhook,
                    text=f"*Bigeye schema changes since {since_time}*",
                    title="Bigeye Schema Changes",
                )

            if webhooks:
                data = {
                    "name": "Bigeye Schema Changes",
                    "since": since_time,
                    "alerts": alert_webhook,
                }
                post_webhook_request(webhook_url=webhooks, data=data)

        if frequency:
            log.info(f"Continuing to track schema changes.")
            log.info(f"The process will run again in {frequency} hours.")
            date_epoch = datetime.now().timestamp()
            time.sleep(frequency * hour_as_secs)
        else:
            log.info("No frequency specified. The process will exit.")
            sys.exit(0)
