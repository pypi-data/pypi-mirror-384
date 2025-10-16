import os
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import typer

from bigeye_cli.functions import cli_client_factory
from bigeye_cli import global_options
from bigeye_cli.bigconfig import bigconfig_options
from bigeye_cli.model.github_report import GitHubReport
from bigeye_sdk.bigconfig_validation.big_config_reports import all_reports
from bigeye_sdk.controller.metric_controller import MetricController
from bigeye_sdk.controller.metric_suite_controller import MetricSuiteController
from bigeye_sdk.generated.com.bigeye.models.generated import MetricInfoList, MetricInfo
from bigeye_sdk.model.big_config import BigConfig
from bigeye_sdk.model.protobuf_message_facade import SimpleCollection
from bigeye_sdk.log import get_logger

log = get_logger(__file__)

app = typer.Typer(no_args_is_help=True, help="Bigconfig Commands for Bigeye CLI")

"""
File should contain commands relating to deploying Bigconfig files.
"""


@app.command()
def plan(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        input_path: Optional[List[str]] = bigconfig_options.input_path,
        output_path: str = bigconfig_options.output_path,
        purge_source_names: Optional[List[str]] = bigconfig_options.purge_source_names,
        purge_all_sources: bool = bigconfig_options.purge_all_sources,
        no_queue: bool = bigconfig_options.no_queue,
        recursive: bool = bigconfig_options.recursive,
        strict_mode: bool = bigconfig_options.strict_mode,
        namespace: Optional[str] = bigconfig_options.namespace,
        cicd: bool = typer.Option(
            False,
            "--cicd_report",
            "-cicd",
            help="Add the report to a pull request. (Github only)",
        ),
):
    """Executes a plan for purging sources or processing bigconfig files in the input path/current
    working directory."""

    client = cli_client_factory(bigeye_conf, config_file, workspace)
    mc = MetricSuiteController(client=client)

    # Resolve args to first true or first non None values
    if not input_path:
        input_path = client.config.bigconfig_input_path or [Path.cwd()]
    if not output_path:
        output_path = client.config.bigconfig_output_path or Path.cwd()
    strict_mode = strict_mode or client.config.bigconfig_strict_mode
    namespace = namespace or client.config.bigconfig_namespace

    if purge_source_names or purge_all_sources:
        report = mc.execute_purge(
            purge_source_names=purge_source_names,
            purge_all_sources=purge_all_sources,
            output_path=output_path,
            apply=False,
            namespace=namespace
        )
    else:
        if no_queue:
            log.warning(
                "The --no_queue flag is deprecated. The option will be ignored now and removed in a later version."
            )
        report = mc.execute_bigconfig(
            input_path=input_path,
            output_path=output_path,
            apply=False,
            recursive=recursive,
            strict_mode=strict_mode,
            namespace=namespace
        )
    if cicd:
        gh_report = GitHubReport(github_token=os.environ["GITHUB_TOKEN"])
        gh_report.publish_bigconfig(console_report=report, file_reports=all_reports())


@app.command()
def apply(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        input_path: Optional[List[str]] = bigconfig_options.input_path,
        output_path: str = bigconfig_options.output_path,
        purge_source_names: Optional[List[str]] = bigconfig_options.purge_source_names,
        purge_all_sources: bool = bigconfig_options.purge_all_sources,
        no_queue: bool = bigconfig_options.no_queue,
        recursive: bool = bigconfig_options.recursive,
        strict_mode: bool = bigconfig_options.strict_mode,
        auto_approve: bool = bigconfig_options.auto_approve,
        namespace: Optional[str] = bigconfig_options.namespace
):
    """Applies a purge of deployed metrics or applies Bigconfig files from the input path/current working directory to
    the Bigeye workspace."""

    client = cli_client_factory(bigeye_conf, config_file, workspace)
    mc = MetricSuiteController(client=client)

    # Resolve args to first true or first non None values
    if not input_path:
        input_path = client.config.bigconfig_input_path or [Path.cwd()]
    if not output_path:
        output_path = client.config.bigconfig_output_path or Path.cwd()
    strict_mode = strict_mode or client.config.bigconfig_strict_mode
    auto_approve = auto_approve or client.config.bigconfig_auto_approve
    namespace = namespace or client.config.bigconfig_namespace

    if purge_source_names or purge_all_sources:
        mc.execute_purge(
            purge_source_names=purge_source_names,
            purge_all_sources=purge_all_sources,
            output_path=output_path,
            apply=True,
            namespace=namespace
        )
    else:
        if no_queue:
            log.warning(
                "The --no_queue flag is deprecated. The option will be ignored now and removed in a later version."
            )
        mc.execute_bigconfig(
            input_path=input_path,
            output_path=output_path,
            apply=True,
            recursive=recursive,
            strict_mode=strict_mode,
            auto_approve=auto_approve,
            namespace=namespace
        )


@app.command()
def export(
        bigeye_conf: str = global_options.bigeye_conf,
        config_file: str = global_options.config_file,
        workspace: str = global_options.workspace,
        output_path: str = bigconfig_options.output_path,
        namespace: Optional[str] = bigconfig_options.namespace,
        auto_apply_on_indexing: bool = typer.Option(
            False, "--auto_apply_on_indexing", "-add_auto", help="Adds section to output"
        ),
        smd_library_path: str = typer.Option(
            "saved_metric_definitions.yaml",
            "--smd-library_path",
            "-smd_path",
            help="Path to the Saved Metric Definition library."
        ),
        smd_only: bool = typer.Option(
            False, "--smd-only", help="Only export metrics to the Saved Metric Definition library"
        ),
        collection_id: int = typer.Option(
            None, "--collection_id", "-cid", help="Collection ID of metrics to be exported."
        ),
        table_id: int = typer.Option(
            None, "--table_id", "-tid", help="Table ID of metrics to be exported."
        ),
        metric_ids: List[int] = typer.Option(
            None, "--metric_id", "-mid", help="Metric ID of metrics to be exported."
        ),
        use_v1: bool = typer.Option(
            False, "--use_v1", "-v1", help="Export metrics using the v1 converter (not recommended)."
        )
):
    """Exports existing metrics into a valid Bigconfig file."""

    client = cli_client_factory(bigeye_conf, config_file, workspace)
    mc = MetricController(client=client, saved_metric_definitions_path=smd_library_path)

    collection: SimpleCollection = SimpleCollection(
        name=f"CLI Export {datetime.today().strftime('%Y%m%d')}", description="SDK Generated"
    )

    final_metric_ids: List[int] = []

    # Require at least 1 option to be specified
    if not collection_id and not table_id and not metric_ids:
        raise typer.BadParameter(
            "At least 1 option must be provided for bigconfig export. Please provide the "
            "collection id (-cid), table id (-tid), or list of metric ids (-mid). "
        )

    # Add metric ids if passed
    if metric_ids:
        final_metric_ids.extend(metric_ids)

    # Get existing collection if passed
    if collection_id:
        collection: SimpleCollection = SimpleCollection.from_datawatch_object(
            client.get_collection(collection_id=collection_id).collection
        )
        final_metric_ids.extend(collection.metric_ids)

    # Get metrics from table if passed
    if table_id:
        metrics_from_table = client.get_metric_info_batch_post(
            table_ids=[table_id]
        ).metrics
        final_metric_ids.extend([m.metric_configuration.id for m in metrics_from_table])
        if not metrics_from_table:
            raise typer.BadParameter(
                f"No metrics found for given table id. Please check arguments and try again."
            )
        if not collection_id:
            collection.name = metrics_from_table[0].metric_metadata.dataset_name

    # Pull raw metric info. Converting to protobuf objects complicates default and zero values unnecessarily
    raw_metrics: List[dict] = client.get_metric_info_batch_post(metric_ids=final_metric_ids,
                                                                    return_raw_response=True)

    if namespace:
        log.info(f"Filtering metrics that only reside in the namespace: {namespace}")
        raw_metrics = []
        # 2025-09-26: Some metric configs don't have the key 'bigconfigNamespace' in them
        for m in raw_metrics:
            cfg = m.get("metricConfiguration")
            if "bigconfigNamespace" in cfg and cfg.get("bigconfigNamespace") == namespace:
                raw_metrics.append(m)
        log.info(f"{len(raw_metrics)} metrics found in namespace: {namespace}")

    if not output_path:
        output_path = client.config.bigconfig_output_path or Path.cwd()

    if not raw_metrics:
        raise typer.BadParameter(
            "No metrics found for given arguments. Please check again."
        )


    if not use_v1:
        mc.infos_to_convert = raw_metrics
        template_smds = mc.collect_template_smds_from_inputs()
        mc.write_or_update_smd_library(
            template_smds_from_inputs=template_smds, auto_apply=auto_apply_on_indexing
        )
        typer.secho(
            f"\nUpdated SMD library at: {mc.saved_metric_def_path}\n", fg="green", bold=True
        )

        if smd_only:
            raise typer.Exit(0)

        bc = mc.to_bigconfig_yaml(collection=collection, auto_apply_on_indexing=auto_apply_on_indexing)

        # Dumping **kwargs messes up the formatting
        bigconfig = BigConfig(type=bc["type"])

        if bc.get("auto_apply_on_indexing", None):
            bigconfig.auto_apply_on_indexing = True
        if bc.get("tag_definitions", None):
            bigconfig.tag_definitions = bc.get("tag_definitions")

        bigconfig.tag_deployments = bc.get("tag_deployments")
    else:
        bigconfig = mc.metric_info_to_bigconfig(
            metric_info=MetricInfoList(metrics=[MetricInfo().from_dict(m) for m in raw_metrics]), collection=collection
        )

    file_name = collection.name.lower().replace(" ", "_")
    output = bigconfig.save(
        output_path=output_path,
        default_file_name=f"{file_name}.bigconfig",
        custom_formatter=bigconfig.format_bigconfig_export,
    )
    typer.secho(
        f"\nBigconfig file generated at: {output}\n", fg="green", bold=True
    )
