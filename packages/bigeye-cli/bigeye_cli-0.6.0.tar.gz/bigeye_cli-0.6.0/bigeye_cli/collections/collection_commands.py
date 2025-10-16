# create logger
from os import listdir
from os.path import join, isfile
from typing import List, Optional, Dict

import smart_open
import typer

from bigeye_cli.functions import cli_client_factory, write_debug_queries
from bigeye_cli import global_options
from bigeye_sdk.generated.com.bigeye.models.generated import (
    TableList,
    Table,
    MetricInfo,
)
from bigeye_sdk.model.collection_models import CollectionMetrics

from bigeye_sdk.log import get_logger
from bigeye_sdk.functions.file_functs import serialize_listdict_to_json_file

log = get_logger(__file__)

app = typer.Typer(no_args_is_help=True, help="Collections Commands for Bigeye CLI")


@app.command()
def add_metric(
    bigeye_conf: str = global_options.bigeye_conf,
    config_file: str = global_options.config_file,
    workspace: str = global_options.workspace,
    metric_ids: List[int] = typer.Option(..., "--metric_id", "-mid", help="Metric ID"),
    collection_id: int = typer.Option(
        ..., "--collection_id", "-cid", help="Collection ID"
    ),
):
    """Add metric to a Collection."""
    log.info(f"Adding metric to Collection.")
    log.info(
        f"Bigeye API Configuration: {bigeye_conf} | Metric IDs: {metric_ids} | Collection ID: {collection_id}"
    )

    client = cli_client_factory(bigeye_conf, config_file, workspace)

    client.upsert_metric_to_collection(
        add_metric_ids=metric_ids, collection_id=collection_id
    )


@app.command()
def get_metric_info(
    bigeye_conf: str = global_options.bigeye_conf,
    config_file: str = global_options.config_file,
    workspace: str = global_options.workspace,
    from_collections: bool = typer.Option(
        False,
        "--from_collections",
        help="Scrapes all Collections in customer workspace for Metric Info.",
    ),
    collection_ids: Optional[List[int]] = typer.Option(
        None,
        "--collection_ids",
        help="Collection IDs.  Scrape certain Collections for Metric Info.",
    ),
    output_path: str = typer.Option(
        ...,
        "--output_path",
        "-op",
        help="File to write the failed metric configurations to.",
    ),
):
    """Get metric info for all metrics in Collection."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)
    collections = client.get_collections()
    collections_to_migrate = (
        [c for c in collections.collections if c.id in collection_ids]
        if not from_collections
        else collections.collections
    )

    for c in collections_to_migrate:
        collection_metric = CollectionMetrics(
            c, client.get_metric_info_batch_post(metric_ids=c.metric_ids)
        )

        url = f"{output_path}/{c.name}.json"

        serialize_listdict_to_json_file(url=url, data=[collection_metric.as_dict()])


@app.command()
def migrate_from_json(
    bigeye_conf: str = global_options.bigeye_conf,
    config_file: str = global_options.config_file,
    workspace: str = global_options.workspace,
    target_warehouse_id: int = typer.Option(
        ...,
        "--target_warehouse_id",
        "-twid",
        help="Deploy Metrics to target Warehouse ID.",
    ),
    input_path: str = typer.Option(
        ..., "--input_path", "-ip", help="Path to read from."
    ),
    keep_notifications: bool = typer.Option(
        False,
        "--keep_notifications",
        "-kn",
        help="Keep Notifications from versioned or templated metric configuration.",
    ),
    keep_ids: bool = typer.Option(
        False,
        "--keep_ids",
        "-kid",
        help="Keep Metric and Collection IDs from versioned or templated metric configuration.  "
        "If kept this would update existing metrics and collections.  If not kept it would "
        "create new.",
    ),
):
    """Loads metrics from Collection oriented metric info output.  Used to migrate metrics from one warehouse to
    another, identical, warehouse"""
    client = cli_client_factory(bigeye_conf, config_file, workspace)

    all_files = [
        join(input_path, f)
        for f in listdir(input_path)
        if isfile(join(input_path, f)) and ".json" in f
    ]

    def open_collection_metrics(file) -> CollectionMetrics:
        with smart_open.open(file) as fin:
            return CollectionMetrics.from_json(fin.read())

    for f in all_files:
        """One Collection per File."""
        collection_metrics = open_collection_metrics(f)

        # Clearing workspace specific settings.
        if not keep_notifications:
            collection_metrics.collection.id = None
        collection_metrics.collection.entity_info = None
        collection_metrics.collection.owner = None
        if not keep_ids:
            collection_metrics.collection.metric_ids = []
        if keep_notifications:
            collection_metrics.collection.notification_channels = []
        m: MetricInfo
        for m in collection_metrics.metrics.metrics:
            if not keep_ids:
                m.metric_configuration.id = None
            if not keep_notifications:
                m.metric_configuration.notification_channels = []

        table_names = {
            m.metric_metadata.dataset_name for m in collection_metrics.metrics.metrics
        }

        tables: TableList = client.get_tables(
            warehouse_id=[target_warehouse_id], table_name=list(table_names)
        )

        t_ix: Dict[str, Table] = {t.name: t for t in tables.tables}

        for m in collection_metrics.metrics.metrics:
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
                )

                collection_metrics.collection.metric_ids.append(rmc.id)

            except Exception as e:
                log.exception(
                    f"Error for Collection: {collection_metrics.collection.name}"
                )
                log.exception(e)

        client.create_collection_dep(collection_metrics.collection)


@app.command()
def backfill_metrics(
    bigeye_conf: str = global_options.bigeye_conf,
    config_file: str = global_options.config_file,
    workspace: str = global_options.workspace,
    from_collections: bool = typer.Option(
        False,
        "--from_collections",
        help="Scrapes all Collections in customer workspace for Metric Info.",
    ),
    collection_ids: Optional[List[int]] = typer.Option(
        None,
        "--collection_ids",
        help="Collection IDs.  Scrape certain Collections for Metric Info.",
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
    """Backfill all metrics in a Collection."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)
    collections = client.get_collections()
    collections_to_migrate = (
        [c for c in collections.collections if c.id in collection_ids]
        if not from_collections
        else collections
    )

    mids = []

    collectionids = []

    for c in collections_to_migrate.collections:
        collection_metrics = CollectionMetrics(
            c, client.get_metric_info_batch_post(metric_ids=c.metric_ids)
        )
        mids.extend(
            [m.metric_configuration.id for m in collection_metrics.metrics.metrics]
        )
        collectionids.append(c.id)

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
    collection_id: int = typer.Option(
        ..., "--collection_id", "-cid", help="Collection ID"
    ),
    queue: bool = typer.Option(
        False,
        "--queue",
        "-q",
        help="Submit the batch to a queue. (Recommended for larger batches)",
    )
):
    """Run all metrics in a Collection."""
    client = cli_client_factory(bigeye_conf, config_file, workspace)
    collection = client.get_collection(collection_id=collection_id)
    mids: List[int] = collection.collection.metric_ids
    client.batch_run_metrics(metric_ids=mids, queue=queue)


@app.command()
def get_metric_queries(
    bigeye_conf: str = global_options.bigeye_conf,
    config_file: str = global_options.config_file,
    workspace: str = global_options.workspace,
    collection_id: int = typer.Option(
        ..., "--collection_id", "-cid", help="Collection ID"
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

    collection = client.get_collection(collection_id=collection_id)
    mids: List[int] = collection.collection.metric_ids

    r = client.get_debug_queries(metric_ids=mids)

    write_debug_queries(output_path=output_path, queries=r)
