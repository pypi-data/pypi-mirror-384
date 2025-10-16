from typing import ClassVar
from typing import Optional

from amsdal.models.mixins import TimestampMixin
from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class CheckpointWrites(TimestampMixin, Model):
    """AMSDAL model for storing checkpoint write operations."""

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    __table_name__ = 'checkpoint_writes'
    __primary_key__: ClassVar[list[str]] = ['thread_id', 'checkpoint_ns', 'checkpoint_id', 'task_id', 'idx']

    thread_id: str = Field(..., title='Thread ID')
    checkpoint_ns: str = Field(default='', title='Checkpoint Namespace')
    checkpoint_id: str = Field(..., title='Checkpoint ID')
    task_id: str = Field(..., title='Task ID')
    idx: int = Field(..., title='Index')
    channel: str = Field(..., title='Channel')
    type: Optional[str] = Field(default=None, title='Type')
    value: Optional[bytes] = Field(default=None, title='Value')
