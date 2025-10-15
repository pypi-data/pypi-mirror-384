import json

import click
from click.core import Context as ClickContext
from loguru import logger
from pydantic import ValidationError

from gable.api.client import GableAPIClient
from gable.cli.helpers.s3 import start_sca_run, upload_sca_results
from gable.cli.options import global_options
from gable.common_types import LineageDataFile
from gable.openapi import CrossServiceDataStore, CrossServiceEdge


def get_lineage_schema(upload_type: str | None):
    if upload_type == "DATA_STORE":
        return CrossServiceDataStore
    elif upload_type == "EDGE":
        return CrossServiceEdge
    return LineageDataFile


@click.command(
    add_help_option=False,
    name="upload",
    epilog="""Example:
    gable lineage upload --project-root ./path/to/project""",
)
@global_options(add_endpoint_options=False)
@click.option(
    "--project-root",
    help="The root directory of the project that will be analyzed.",
    type=click.Path(exists=True),
    required=True,
)
@click.option(
    "--results-file",
    help="The path to the results file.",
    type=click.Path(exists=True),
    required=True,
)
@click.pass_context
def lineage_upload(
    ctx: ClickContext,
    project_root: str,
    results_file: str,
):
    """
    Upload lineage data to Gable.
    """
    client: GableAPIClient = ctx.obj.client
    with open(results_file, "r") as f:
        results = json.load(f)
    try:
        upload_type = results.get("type")
        LineageFile = get_lineage_schema(upload_type)
        lineage_obj = LineageFile.model_validate(results)
    except ValidationError as e:
        logger.debug(f"Invalid results file: {e}")
        raise click.ClickException(f"Invalid results file: {e}")

    external_component_id = getattr(lineage_obj, "external_component_id", None)
    repo_name = getattr(lineage_obj, "name", None)

    run_id, presigned_url = start_sca_run(
        client,
        project_root,
        "upload",
        None,
        None,
        external_component_id,
        upload_type,
        repo_name,
    )
    upload_sca_results(run_id, presigned_url, lineage_obj)
    click.echo(
        f"Uploaded lineage data from {results_file} to Gable with run ID: {run_id}"
    )
