from amsdal_models.migration import migrations
from amsdal_utils.models.enums import ModuleType


class Migration(migrations.Migration):
    operations: list[migrations.Operation] = [
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="Checkpoint",
            new_schema={
                "title": "Checkpoint",
                "required": ["thread_id", "checkpoint_id", "checkpoint"],
                "properties": {
                    "created_at": {"type": "datetime", "title": "Created At", "format": "date-time"},
                    "updated_at": {"type": "datetime", "title": "Updated At", "format": "date-time"},
                    "thread_id": {"type": "string", "title": "Thread ID"},
                    "checkpoint_ns": {"type": "string", "default": "", "title": "Checkpoint Namespace"},
                    "checkpoint_id": {"type": "string", "title": "Checkpoint ID"},
                    "parent_checkpoint_id": {"type": "string", "title": "Parent Checkpoint ID"},
                    "type": {"type": "string", "title": "Type"},
                    "checkpoint": {"type": "binary", "title": "Checkpoint Data"},
                    "meta": {
                        "type": "dictionary",
                        "items": {"key": {"type": "string"}, "value": {"type": "anything"}},
                        "title": "Metadata",
                    },
                },
                "custom_code": "import datetime\n\n\nasync def apre_create(self) -> None:\n    self.created_at = datetime.datetime.now(tz=datetime.UTC)\n    await super().apre_create()\n\nasync def apre_update(self) -> None:\n    self.updated_at = datetime.datetime.now(tz=datetime.UTC)\n    if not self.created_at:\n        _metadata = await self.aget_metadata()\n        self.created_at = datetime.datetime.fromtimestamp(_metadata.created_at / 1000, tz=datetime.UTC)\n    await super().apre_update()\n\ndef pre_create(self) -> None:\n    self.created_at = datetime.datetime.now(tz=datetime.UTC)\n    super().pre_create()\n\ndef pre_update(self) -> None:\n    self.updated_at = datetime.datetime.now(tz=datetime.UTC)\n    if not self.created_at:\n        _metadata = self.get_metadata()\n        self.created_at = datetime.datetime.fromtimestamp(_metadata.created_at / 1000, tz=datetime.UTC)\n    super().pre_update()",
                "storage_metadata": {
                    "table_name": "checkpoints",
                    "db_fields": {},
                    "primary_key": ["thread_id", "checkpoint_ns", "checkpoint_id"],
                    "foreign_keys": {},
                },
                "description": "AMSDAL model for storing LangGraph checkpoints.",
            },
        ),
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="CheckpointWrites",
            new_schema={
                "title": "CheckpointWrites",
                "required": ["thread_id", "checkpoint_id", "task_id", "idx", "channel"],
                "properties": {
                    "created_at": {"type": "datetime", "title": "Created At", "format": "date-time"},
                    "updated_at": {"type": "datetime", "title": "Updated At", "format": "date-time"},
                    "thread_id": {"type": "string", "title": "Thread ID"},
                    "checkpoint_ns": {"type": "string", "default": "", "title": "Checkpoint Namespace"},
                    "checkpoint_id": {"type": "string", "title": "Checkpoint ID"},
                    "task_id": {"type": "string", "title": "Task ID"},
                    "idx": {"type": "integer", "title": "Index"},
                    "channel": {"type": "string", "title": "Channel"},
                    "type": {"type": "string", "title": "Type"},
                    "value": {"type": "binary", "title": "Value"},
                },
                "custom_code": "import datetime\n\n\nasync def apre_create(self) -> None:\n    self.created_at = datetime.datetime.now(tz=datetime.UTC)\n    await super().apre_create()\n\nasync def apre_update(self) -> None:\n    self.updated_at = datetime.datetime.now(tz=datetime.UTC)\n    if not self.created_at:\n        _metadata = await self.aget_metadata()\n        self.created_at = datetime.datetime.fromtimestamp(_metadata.created_at / 1000, tz=datetime.UTC)\n    await super().apre_update()\n\ndef pre_create(self) -> None:\n    self.created_at = datetime.datetime.now(tz=datetime.UTC)\n    super().pre_create()\n\ndef pre_update(self) -> None:\n    self.updated_at = datetime.datetime.now(tz=datetime.UTC)\n    if not self.created_at:\n        _metadata = self.get_metadata()\n        self.created_at = datetime.datetime.fromtimestamp(_metadata.created_at / 1000, tz=datetime.UTC)\n    super().pre_update()",
                "storage_metadata": {
                    "table_name": "checkpoint_writes",
                    "db_fields": {},
                    "primary_key": ["thread_id", "checkpoint_ns", "checkpoint_id", "task_id", "idx"],
                    "foreign_keys": {},
                },
                "description": "AMSDAL model for storing checkpoint write operations.",
            },
        ),
    ]
