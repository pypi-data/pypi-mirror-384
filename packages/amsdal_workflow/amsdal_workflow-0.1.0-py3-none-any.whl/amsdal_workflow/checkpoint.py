import random
from collections.abc import AsyncIterator
from collections.abc import Iterator
from collections.abc import Sequence
from typing import Any
from typing import cast

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import WRITES_IDX_MAP
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.base import ChannelVersions
from langgraph.checkpoint.base import Checkpoint
from langgraph.checkpoint.base import CheckpointMetadata
from langgraph.checkpoint.base import CheckpointTuple
from langgraph.checkpoint.base import get_checkpoint_id
from langgraph.checkpoint.serde.base import SerializerProtocol
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from .models.checkpoint import Checkpoint as CheckpointModel
from .models.checkpoint_writes import CheckpointWrites as CheckpointWritesModel
from .utils import get_checkpoint_metadata
from .utils import search_where


class AmsdalCheckpointSaver(BaseCheckpointSaver[str]):
    """AMSDAL-based checkpoint saver for LangGraph workflows."""

    def __init__(self, *, serde: SerializerProtocol | None = None):
        """Initialize the AMSDAL checkpoint saver.

        Args:
            serde: Optional serializer protocol for checkpoint serialization.
        """
        super().__init__(serde=serde)
        self.jsonplus_serde = JsonPlusSerializer()

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Get a checkpoint tuple synchronously.

        Args:
            config: The runnable configuration.

        Returns:
            The checkpoint tuple or None if not found.
        """
        checkpoint_ns = config['configurable'].get('checkpoint_ns', '')

        # Find the specific checkpoint or latest one
        if checkpoint_id := get_checkpoint_id(config):
            checkpoint_obj = (
                CheckpointModel.objects.filter(
                    thread_id=str(config['configurable']['thread_id']),
                    checkpoint_ns=checkpoint_ns,
                    checkpoint_id=checkpoint_id,
                )
                .first()
                .execute()
            )
        else:
            checkpoint_obj = (
                CheckpointModel.objects.filter(
                    thread_id=str(config['configurable']['thread_id']),
                    checkpoint_ns=checkpoint_ns,
                )
                .order_by('-checkpoint_id')
                .first()
                .execute()
            )

        if not checkpoint_obj:
            return None

        (
            thread_id,
            checkpoint_id,
            parent_checkpoint_id,
            _type,
            checkpoint,
            metadata,
        ) = (
            checkpoint_obj.thread_id,
            checkpoint_obj.checkpoint_id,
            checkpoint_obj.parent_checkpoint_id,
            checkpoint_obj.type,
            checkpoint_obj.checkpoint,
            checkpoint_obj.meta,
        )

        if not get_checkpoint_id(config):
            config = {
                'configurable': {
                    'thread_id': thread_id,
                    'checkpoint_ns': checkpoint_ns,
                    'checkpoint_id': checkpoint_id,
                }
            }

        # Get pending writes for this checkpoint
        writes = (
            CheckpointWritesModel.objects.filter(
                thread_id=str(config['configurable']['thread_id']),
                checkpoint_ns=checkpoint_ns,
                checkpoint_id=str(config['configurable']['checkpoint_id']),
            )
            .order_by('task_id', 'idx')
            .execute()
        )

        # deserialize the checkpoint and metadata
        return CheckpointTuple(
            config,
            self.serde.loads_typed((_type, checkpoint)),
            cast(
                CheckpointMetadata,
                metadata if metadata is not None else {},
            ),
            (
                {
                    'configurable': {
                        'thread_id': thread_id,
                        'checkpoint_ns': checkpoint_ns,
                        'checkpoint_id': parent_checkpoint_id,
                    }
                }
                if parent_checkpoint_id
                else None
            ),
            [(write.task_id, write.channel, self.serde.loads_typed((write.type, write.value))) for write in writes],
        )

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,  # noqa: A002, ARG002
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoints synchronously.

        Args:
            config: The runnable configuration.
            filter: Optional filter criteria.
            before: Optional before configuration.
            limit: Optional limit on results.

        Yields:
            Checkpoint tuples.
        """
        query = CheckpointModel.objects.all().order_by('-checkpoint_id')
        where = search_where(config, filter, before)

        if where:
            query = query.filter(where)

        if limit:
            checkpoints = query[0:limit].execute()
        else:
            checkpoints = query.execute()

        for checkpoint_obj in checkpoints:
            writes = (
                CheckpointWritesModel.objects.filter(
                    thread_id=checkpoint_obj.thread_id,
                    checkpoint_ns=checkpoint_obj.checkpoint_ns,
                    checkpoint_id=checkpoint_obj.checkpoint_id,
                )
                .order_by('task_id', 'idx')
                .execute()
            )

            yield CheckpointTuple(
                {
                    'configurable': {
                        'thread_id': checkpoint_obj.thread_id,
                        'checkpoint_ns': checkpoint_obj.checkpoint_ns,
                        'checkpoint_id': checkpoint_obj.checkpoint_id,
                    }
                },
                self.serde.loads_typed((checkpoint_obj.type, checkpoint_obj.checkpoint)),
                cast(
                    CheckpointMetadata,
                    checkpoint_obj.meta if checkpoint_obj.meta is not None else {},
                ),
                (
                    {
                        'configurable': {
                            'thread_id': checkpoint_obj.thread_id,
                            'checkpoint_ns': checkpoint_obj.checkpoint_ns,
                            'checkpoint_id': checkpoint_obj.parent_checkpoint_id,
                        }
                    }
                    if checkpoint_obj.parent_checkpoint_id
                    else None
                ),
                [(write.task_id, write.channel, self.serde.loads_typed((write.type, write.value))) for write in writes],
            )

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,  # noqa: ARG002
    ) -> RunnableConfig:
        """Put a checkpoint synchronously.

        Args:
            config: The runnable configuration.
            checkpoint: The checkpoint data.
            metadata: The checkpoint metadata.
            new_versions: The new channel versions.

        Returns:
            The updated runnable configuration.
        """
        thread_id = config['configurable']['thread_id']
        checkpoint_ns = config['configurable']['checkpoint_ns']
        type_, serialized_checkpoint = self.serde.dumps_typed(checkpoint)

        # Create or update checkpoint
        checkpoint_obj = CheckpointModel(
            thread_id=str(config['configurable']['thread_id']),
            checkpoint_ns=checkpoint_ns,
            checkpoint_id=checkpoint['id'],
            parent_checkpoint_id=config['configurable'].get('checkpoint_id'),
            type=type_,
            checkpoint=serialized_checkpoint,
            meta=get_checkpoint_metadata(config, metadata),  # type: ignore[arg-type]
        )

        if (
            CheckpointModel.objects.filter(
                thread_id=str(config['configurable']['thread_id']),
                checkpoint_ns=checkpoint_ns,
                checkpoint_id=checkpoint['id'],
            )
            .count()
            .execute()
        ):
            checkpoint_obj.save()
        else:
            checkpoint_obj.save(force_insert=True)

        return {
            'configurable': {
                'thread_id': thread_id,
                'checkpoint_ns': checkpoint_ns,
                'checkpoint_id': checkpoint['id'],
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = '',  # noqa: ARG002
    ) -> None:
        """Put writes synchronously.

        Args:
            config: The runnable configuration.
            writes: The writes to store.
            task_id: The task ID.
            task_path: The task path.
        """
        _replace = all(w[0] in WRITES_IDX_MAP for w in writes)

        for idx, (channel, value) in enumerate(writes):
            type_name, serialized_value = self.serde.dumps_typed(value)
            write_obj = CheckpointWritesModel(
                thread_id=str(config['configurable']['thread_id']),
                checkpoint_ns=str(config['configurable']['checkpoint_ns']),
                checkpoint_id=str(config['configurable']['checkpoint_id']),
                task_id=task_id,
                idx=WRITES_IDX_MAP.get(channel, idx),
                channel=channel,
                type=type_name,
                value=serialized_value,
            )

            if (
                CheckpointWritesModel.objects.filter(
                    thread_id=str(config['configurable']['thread_id']),
                    checkpoint_ns=str(config['configurable']['checkpoint_ns']),
                    checkpoint_id=str(config['configurable']['checkpoint_id']),
                    task_id=task_id,
                    idx=WRITES_IDX_MAP.get(channel, idx),
                )
                .count()
                .execute()
            ):
                if _replace:
                    write_obj.save()
            else:
                write_obj.save(force_insert=True)

    def delete_thread(self, thread_id: str) -> None:
        """Delete a thread synchronously.

        Args:
            thread_id: The thread ID to delete.
        """
        # Delete all checkpoints for this thread
        checkpoints = CheckpointModel.objects.filter(thread_id=str(thread_id)).execute()

        for checkpoint in checkpoints:
            checkpoint.delete()

        # Delete all writes for this thread
        writes = CheckpointWritesModel.objects.filter(thread_id=str(thread_id)).execute()

        for write in writes:
            write.delete()

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Get a checkpoint tuple asynchronously.

        Args:
            config: The runnable configuration.

        Returns:
            The checkpoint tuple or None if not found.
        """
        checkpoint_ns = config['configurable'].get('checkpoint_ns', '')

        # Find the specific checkpoint or latest one
        if checkpoint_id := get_checkpoint_id(config):
            checkpoint_obj = (
                await CheckpointModel.objects.filter(
                    thread_id=str(config['configurable']['thread_id']),
                    checkpoint_ns=checkpoint_ns,
                    checkpoint_id=checkpoint_id,
                )
                .first()
                .aexecute()
            )
        else:
            checkpoint_obj = await (
                CheckpointModel.objects.filter(
                    thread_id=str(config['configurable']['thread_id']),
                    checkpoint_ns=checkpoint_ns,
                )
                .order_by('-checkpoint_id')
                .first()
                .aexecute()
            )

        if not checkpoint_obj:
            return None

        (
            thread_id,
            checkpoint_id,
            parent_checkpoint_id,
            _type,
            checkpoint,
            metadata,
        ) = (
            checkpoint_obj.thread_id,
            checkpoint_obj.checkpoint_id,
            checkpoint_obj.parent_checkpoint_id,
            checkpoint_obj.type,
            checkpoint_obj.checkpoint,
            checkpoint_obj.meta,
        )

        if not get_checkpoint_id(config):
            config = {
                'configurable': {
                    'thread_id': thread_id,
                    'checkpoint_ns': checkpoint_ns,
                    'checkpoint_id': checkpoint_id,
                }
            }

        # Get pending writes for this checkpoint
        writes = await (
            CheckpointWritesModel.objects.filter(
                thread_id=str(config['configurable']['thread_id']),
                checkpoint_ns=checkpoint_ns,
                checkpoint_id=str(config['configurable']['checkpoint_id']),
            )
            .order_by('task_id', 'idx')
            .aexecute()
        )

        # deserialize the checkpoint and metadata
        return CheckpointTuple(
            config,
            self.serde.loads_typed((_type, checkpoint)),
            cast(
                CheckpointMetadata,
                metadata if metadata is not None else {},
            ),
            (
                {
                    'configurable': {
                        'thread_id': thread_id,
                        'checkpoint_ns': checkpoint_ns,
                        'checkpoint_id': parent_checkpoint_id,
                    }
                }
                if parent_checkpoint_id
                else None
            ),
            [(write.task_id, write.channel, self.serde.loads_typed((write.type, write.value))) for write in writes],
        )

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,  # noqa: A002, ARG002
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """List checkpoints asynchronously.

        Args:
            config: The runnable configuration.
            filter: Optional filter criteria.
            before: Optional before configuration.
            limit: Optional limit on results.

        Yields:
            Checkpoint tuples.
        """
        query = CheckpointModel.objects.all().order_by('-checkpoint_id')
        where = search_where(config, filter, before)

        if where:
            query = query.filter(where)

        if limit:
            checkpoints = await query[:limit].aexecute()
        else:
            checkpoints = await query.aexecute()

        for checkpoint_obj in checkpoints:
            writes = await (
                CheckpointWritesModel.objects.filter(
                    thread_id=checkpoint_obj.thread_id,
                    checkpoint_ns=checkpoint_obj.checkpoint_ns,
                    checkpoint_id=checkpoint_obj.checkpoint_id,
                )
                .order_by('task_id', 'idx')
                .aexecute()
            )

            yield CheckpointTuple(
                {
                    'configurable': {
                        'thread_id': checkpoint_obj.thread_id,
                        'checkpoint_ns': checkpoint_obj.checkpoint_ns,
                        'checkpoint_id': checkpoint_obj.checkpoint_id,
                    }
                },
                self.serde.loads_typed((checkpoint_obj.type, checkpoint_obj.checkpoint)),
                cast(
                    CheckpointMetadata,
                    checkpoint_obj.meta if checkpoint_obj.meta is not None else {},
                ),
                (
                    {
                        'configurable': {
                            'thread_id': checkpoint_obj.thread_id,
                            'checkpoint_ns': checkpoint_obj.checkpoint_ns,
                            'checkpoint_id': checkpoint_obj.parent_checkpoint_id,
                        }
                    }
                    if checkpoint_obj.parent_checkpoint_id
                    else None
                ),
                [(write.task_id, write.channel, self.serde.loads_typed((write.type, write.value))) for write in writes],
            )

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,  # noqa: ARG002
    ) -> RunnableConfig:
        """Put a checkpoint asynchronously.

        Args:
            config: The runnable configuration.
            checkpoint: The checkpoint data.
            metadata: The checkpoint metadata.
            new_versions: The new channel versions.

        Returns:
            The updated runnable configuration.
        """
        thread_id = config['configurable']['thread_id']
        checkpoint_ns = config['configurable']['checkpoint_ns']
        type_, serialized_checkpoint = self.serde.dumps_typed(checkpoint)

        # Create or update checkpoint
        checkpoint_obj = CheckpointModel(
            thread_id=str(config['configurable']['thread_id']),
            checkpoint_ns=checkpoint_ns,
            checkpoint_id=checkpoint['id'],
            parent_checkpoint_id=config['configurable'].get('checkpoint_id'),
            type=type_,
            checkpoint=serialized_checkpoint,
            meta=get_checkpoint_metadata(config, metadata),  # type: ignore[arg-type]
        )

        if (
            await CheckpointModel.objects.filter(
                thread_id=str(config['configurable']['thread_id']),
                checkpoint_ns=checkpoint_ns,
                checkpoint_id=checkpoint['id'],
            )
            .count()
            .aexecute()
        ):
            await checkpoint_obj.asave()  # type: ignore[misc]
        else:
            await checkpoint_obj.asave(force_insert=True)  # type: ignore[misc]

        return {
            'configurable': {
                'thread_id': thread_id,
                'checkpoint_ns': checkpoint_ns,
                'checkpoint_id': checkpoint['id'],
            }
        }

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = '',  # noqa: ARG002
    ) -> None:
        """Put writes asynchronously.

        Args:
            config: The runnable configuration.
            writes: The writes to store.
            task_id: The task ID.
            task_path: The task path.
        """
        _replace = all(w[0] in WRITES_IDX_MAP for w in writes)

        for idx, (channel, value) in enumerate(writes):
            type_name, serialized_value = self.serde.dumps_typed(value)
            write_obj = CheckpointWritesModel(
                thread_id=str(config['configurable']['thread_id']),
                checkpoint_ns=str(config['configurable']['checkpoint_ns']),
                checkpoint_id=str(config['configurable']['checkpoint_id']),
                task_id=task_id,
                idx=WRITES_IDX_MAP.get(channel, idx),
                channel=channel,
                type=type_name,
                value=serialized_value,
            )

            if await (
                CheckpointWritesModel.objects.filter(
                    thread_id=str(config['configurable']['thread_id']),
                    checkpoint_ns=str(config['configurable']['checkpoint_ns']),
                    checkpoint_id=str(config['configurable']['checkpoint_id']),
                    task_id=task_id,
                    idx=WRITES_IDX_MAP.get(channel, idx),
                )
                .count()
                .aexecute()
            ):
                if _replace:
                    await write_obj.asave()  # type: ignore[misc]
            else:
                await write_obj.asave(force_insert=True)  # type: ignore[misc]

    async def adelete_thread(self, thread_id: str) -> None:
        """Delete a thread asynchronously.

        Args:
            thread_id: The thread ID to delete.
        """
        # Delete all checkpoints for this thread
        checkpoints = await CheckpointModel.objects.filter(thread_id=str(thread_id)).aexecute()

        for checkpoint in checkpoints:
            await checkpoint.adelete()

        # Delete all writes for this thread
        writes = await CheckpointWritesModel.objects.filter(thread_id=str(thread_id)).aexecute()

        for write in writes:
            await write.adelete()

    def get_next_version(self, current: str | None, channel: None) -> str:  # noqa: ARG002
        """Generate the next version ID for a channel.

        This method creates a new version identifier for a channel based on its current version.

        Args:
            current (Optional[str]): The current version identifier of the channel.

        Returns:
            str: The next version identifier, which is guaranteed to be monotonically increasing.
        """
        if current is None:
            current_v = 0
        elif isinstance(current, int):
            current_v = current
        else:
            current_v = int(current.split('.')[0])
        next_v = current_v + 1
        next_h = random.random()  # noqa: S311
        return f'{next_v:032}.{next_h:016}'
