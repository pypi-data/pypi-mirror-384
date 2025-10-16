from __future__ import annotations

from typing import cast

from infrahub_sdk.template import Jinja2Template
from prefect import flow
from prefect.logging import get_run_logger

from infrahub.context import InfrahubContext  # noqa: TC001  needed for prefect flow
from infrahub.core.registry import registry
from infrahub.events import BranchDeletedEvent
from infrahub.trigger.models import TriggerSetupReport, TriggerType
from infrahub.trigger.setup import setup_triggers_specific
from infrahub.workers.dependencies import get_client, get_component, get_database, get_workflow
from infrahub.workflows.catalogue import DISPLAY_LABELS_PROCESS_JINJA2, TRIGGER_UPDATE_DISPLAY_LABELS
from infrahub.workflows.utils import add_tags, wait_for_schema_to_converge

from .gather import gather_trigger_display_labels_jinja2
from .models import DisplayLabelJinja2GraphQL, DisplayLabelJinja2GraphQLResponse, DisplayLabelTriggerDefinition

UPDATE_DISPLAY_LABEL = """
mutation UpdateDisplayLabel(
    $id: String!,
    $kind: String!,
    $value: String!
  ) {
  InfrahubUpdateDisplayLabel(
    data: {id: $id, value: $value, kind: $kind}
  ) {
    ok
  }
}
"""


@flow(
    name="display-label-jinja2-update-value",
    flow_run_name="Update value for display_label on {node_kind}",
)
async def display_label_jinja2_update_value(
    branch_name: str,
    obj: DisplayLabelJinja2GraphQLResponse,
    node_kind: str,
    template: Jinja2Template,
) -> None:
    log = get_run_logger()
    client = get_client()

    await add_tags(branches=[branch_name], nodes=[obj.node_id], db_change=True)

    value = await template.render(variables=obj.variables)
    if value == obj.display_label_value:
        log.debug(f"Ignoring to update {obj} with existing value on display_label={value}")
        return

    await client.execute_graphql(
        query=UPDATE_DISPLAY_LABEL,
        variables={"id": obj.node_id, "kind": node_kind, "value": value},
        branch_name=branch_name,
    )
    log.info(f"Updating {node_kind}.display_label='{value}' ({obj.node_id})")


@flow(
    name="display-label-process-jinja2",
    flow_run_name="Process display_labels for {target_kind}",
)
async def process_display_label(
    branch_name: str,
    node_kind: str,
    object_id: str,
    target_kind: str,
    context: InfrahubContext,  # noqa: ARG001
) -> None:
    log = get_run_logger()
    client = get_client()

    await add_tags(branches=[branch_name])

    target_schema = branch_name if branch_name in registry.get_altered_schema_branches() else registry.default_branch
    schema_branch = registry.schema.get_schema_branch(name=target_schema)
    node_schema = schema_branch.get_node(name=target_kind, duplicate=False)

    if node_kind == target_kind:
        display_label_template = schema_branch.display_labels.get_template_node(kind=node_kind)
    else:
        display_label_template = schema_branch.display_labels.get_related_template(
            related_kind=node_kind, target_kind=target_kind
        )

    jinja_template = Jinja2Template(template=display_label_template.template)
    variables = jinja_template.get_variables()
    display_label_graphql = DisplayLabelJinja2GraphQL(
        node_schema=node_schema, variables=variables, filter_key=display_label_template.filter_key
    )

    query = display_label_graphql.render_graphql_query(filter_id=object_id)
    response = await client.execute_graphql(query=query, branch_name=branch_name)
    update_candidates = display_label_graphql.parse_response(response=response)

    if not update_candidates:
        log.debug("No nodes found that requires updates")
        return

    batch = await client.create_batch()
    for node in update_candidates:
        batch.add(
            task=display_label_jinja2_update_value,
            branch_name=branch_name,
            obj=node,
            node_kind=node_schema.kind,
            template=jinja_template,
        )

    _ = [response async for _, response in batch.execute()]


@flow(name="display-labels-setup-jinja2", flow_run_name="Setup display labels in task-manager")
async def display_labels_setup_jinja2(
    context: InfrahubContext, branch_name: str | None = None, event_name: str | None = None
) -> None:
    database = await get_database()
    async with database.start_session() as db:
        log = get_run_logger()

        if branch_name:
            await add_tags(branches=[branch_name])
            component = await get_component()
            await wait_for_schema_to_converge(branch_name=branch_name, component=component, db=db, log=log)

        report: TriggerSetupReport = await setup_triggers_specific(
            gatherer=gather_trigger_display_labels_jinja2, trigger_type=TriggerType.DISPLAY_LABEL_JINJA2
        )  # type: ignore[misc]

        # Configure all DisplayLabelTriggerDefinitions in Prefect
        display_reports = [cast(DisplayLabelTriggerDefinition, entry) for entry in report.updated + report.created]
        direct_target_triggers = [display_report for display_report in display_reports if display_report.target_kind]

        for display_report in direct_target_triggers:
            if event_name != BranchDeletedEvent.event_name and display_report.branch == branch_name:
                await get_workflow().submit_workflow(
                    workflow=TRIGGER_UPDATE_DISPLAY_LABELS,
                    context=context,
                    parameters={
                        "branch_name": display_report.branch,
                        "kind": display_report.target_kind,
                    },
                )

        log.info(f"{report.in_use_count} Display labels for Jinja2 automation configuration completed")


@flow(
    name="trigger-update-display-labels",
    flow_run_name="Trigger updates for display labels for kind",
)
async def trigger_update_display_labels(
    branch_name: str,
    kind: str,
    context: InfrahubContext,
) -> None:
    await add_tags(branches=[branch_name])

    client = get_client()

    # NOTE we only need the id of the nodes, this query will still query for the HFID
    node_schema = registry.schema.get_node_schema(name=kind, branch=branch_name)
    nodes = await client.all(
        kind=kind,
        branch=branch_name,
        exclude=node_schema.attribute_names + node_schema.relationship_names,
        populate_store=False,
    )

    for node in nodes:
        await get_workflow().submit_workflow(
            workflow=DISPLAY_LABELS_PROCESS_JINJA2,
            context=context,
            parameters={
                "branch_name": branch_name,
                "node_kind": kind,
                "target_kind": kind,
                "object_id": node.id,
                "context": context,
            },
        )
