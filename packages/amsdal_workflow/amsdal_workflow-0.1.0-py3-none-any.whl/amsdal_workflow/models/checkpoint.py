from typing import Any
from typing import ClassVar
from typing import Optional

from amsdal.models.mixins import TimestampMixin
from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class Checkpoint(TimestampMixin, Model):
    """AMSDAL model for storing LangGraph checkpoints."""

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    __table_name__ = 'checkpoints'
    __primary_key__: ClassVar[list[str]] = ['thread_id', 'checkpoint_ns', 'checkpoint_id']

    thread_id: str = Field(..., title='Thread ID')
    checkpoint_ns: str = Field(default='', title='Checkpoint Namespace')
    checkpoint_id: str = Field(..., title='Checkpoint ID')
    parent_checkpoint_id: Optional[str] = Field(default=None, title='Parent Checkpoint ID')
    type: Optional[str] = Field(default=None, title='Type')
    checkpoint: bytes = Field(..., title='Checkpoint Data')
    meta: dict[str, Any | None] | None = Field(..., title='Metadata')
