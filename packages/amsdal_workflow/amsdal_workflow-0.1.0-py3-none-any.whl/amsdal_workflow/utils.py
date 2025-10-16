from typing import Any
from typing import Optional

from amsdal_utils.query.utils import Q
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import EXCLUDED_METADATA_KEYS
from langgraph.checkpoint.base import CheckpointMetadata
from langgraph.checkpoint.base import get_checkpoint_id


def search_where(
    config: RunnableConfig | None,
    filter: dict[str, Any] | None,  # noqa: A002
    before: RunnableConfig | None = None,
) -> Optional[Q]:
    conditions = None

    # construct predicate for config filter
    if config is not None:
        conditions = Q(thread_id=config['configurable']['thread_id'])

        checkpoint_ns = config['configurable'].get('checkpoint_ns')
        if checkpoint_ns is not None:
            conditions &= Q(checkpoint_ns=checkpoint_ns)

        if checkpoint_id := get_checkpoint_id(config):
            conditions &= Q(checkpoint_id=checkpoint_id)

    # construct predicate for metadata filter
    if filter:
        for query_key, query_value in filter.items():
            condition = Q(**{f'meta__{query_key}': query_value})

            if not conditions:
                conditions = condition
            else:
                conditions &= condition

    # construct predicate for `before`
    if before is not None:
        condition = Q(checkpoint_id__lt=get_checkpoint_id(before))

        if not conditions:
            conditions = condition
        else:
            conditions &= condition

    return conditions


def get_checkpoint_metadata(config: RunnableConfig, metadata: CheckpointMetadata) -> CheckpointMetadata:
    """Get checkpoint metadata in a backwards-compatible manner."""
    metadata = {  # type: ignore[assignment]
        k: v.replace('\u0000', '')
        if isinstance(v, str) else v for k, v in metadata.items()
    }
    for obj in (config.get('metadata'), config.get('configurable')):
        if not obj:
            continue
        for key, v in obj.items():
            if key in metadata or key in EXCLUDED_METADATA_KEYS or key.startswith('__'):
                continue
            elif isinstance(v, str):
                metadata[key] = v.replace('\u0000', '')  # type: ignore[literal-required]
            elif isinstance(v, (int, bool, float)):
                metadata[key] = v  # type: ignore[literal-required]
    return metadata
