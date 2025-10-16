import json
from typing import List, Optional

import click

from ..client import HLJSONEncoder
from ..client.base_models.base_models import CaseType
from ..core import GQLBaseModel


class CreateCasePayload(GQLBaseModel):
    errors: List[str]
    case: Optional[CaseType] = None


@click.group("case")
@click.pass_context
def case_group(ctx):
    pass


@case_group.command("create")
@click.option(
    "-w",
    "--workflow-order-id",
    type=str,
    required=True,
    help="Workflow order ID",
)
@click.option(
    "-n",
    "--name",
    type=str,
    required=False,
    help="Case name",
)
@click.option(
    "-e",
    "--entity-id",
    type=str,
    required=False,
    help="Entity ID",
)
@click.option(
    "-f",
    "--initial-data-file-ids",
    type=str,
    required=False,
    help="Initial data file IDs (comma-separated)",
    multiple=True,
)
@click.pass_context
def create(ctx, workflow_order_id, name, entity_id, initial_data_file_ids):
    """Create a new case"""
    client = ctx.obj["client"]

    # Flatten, split, and filter comma-separated IDs
    file_ids = [
        fid.strip() for id_group in initial_data_file_ids for fid in id_group.split(",") if fid.strip()
    ]

    result = client.createCase(
        return_type=CreateCasePayload,
        workflowOrderId=workflow_order_id,
        name=name,
        entityId=entity_id,
        initialDataFileIds=file_ids if file_ids else None,
    ).gql_dict()

    click.echo(json.dumps(result, cls=HLJSONEncoder))

    # Exit with non-zero code if there are errors
    if result.get("errors"):
        raise click.ClickException("Case creation failed")
