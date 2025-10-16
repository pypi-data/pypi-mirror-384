"""Tests for AmsdalCheckpointSaver implementation."""

import shutil
import sqlite3
import tempfile
import uuid
from collections.abc import AsyncIterator
from collections.abc import Iterator
from pathlib import Path

import aiosqlite
import pytest
import pytest_asyncio
from amsdal.manager import AmsdalManager
from amsdal.manager import AsyncAmsdalManager
from amsdal.utils.tests.enums import DbExecutionType
from amsdal.utils.tests.enums import LakehouseOption
from amsdal.utils.tests.enums import StateOption
from amsdal.utils.tests.helpers import async_init_manager_and_migrate
from amsdal.utils.tests.helpers import init_manager_and_migrate
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.base import Checkpoint
from langgraph.checkpoint.base import CheckpointMetadata
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from amsdal_workflow.checkpoint import AmsdalCheckpointSaver

TESTS_DIR = Path(__file__).parent


def _create_temp_models_dir() -> Path:
    """Create temporary directory with modified models for testing."""
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())

    # Copy the entire amsdal_workflow package to temp directory
    source_package = TESTS_DIR.parent / 'amsdal_workflow'
    dest_package = temp_dir / 'amsdal_workflow'
    shutil.copytree(source_package, dest_package)

    # Modify __module_type__ in model files
    models_dir = dest_package / 'models'
    for model_file in models_dir.glob('*.py'):
        if model_file.name == '__init__.py':
            continue

        content = model_file.read_text()
        if '__module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB' in content:
            modified_content = content.replace(
                '__module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB',
                '__module_type__: ClassVar[ModuleType] = ModuleType.USER'
            )
            model_file.write_text(modified_content)

    return temp_dir


@pytest.fixture
def sync_amsdal_manager() -> Iterator[AmsdalManager]:
    """Create sync AmsdalManager instance for testing."""
    temp_dir = _create_temp_models_dir()
    try:
        with init_manager_and_migrate(
            src_dir_path=temp_dir / 'amsdal_workflow',
            db_execution_type=DbExecutionType.include_state_db,
            lakehouse_option=LakehouseOption.sqlite,
            state_option=StateOption.sqlite,
            ACCESS_TOKEN='test_token_for_testing',
        ) as manager:
            yield manager
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest_asyncio.fixture
async def async_amsdal_manager() -> AsyncIterator[AsyncAmsdalManager]:
    """Create async AmsdalManager instance for testing."""
    temp_dir = _create_temp_models_dir()
    try:
        async with async_init_manager_and_migrate(
            src_dir_path=temp_dir / 'amsdal_workflow',
            db_execution_type=DbExecutionType.include_state_db,
            lakehouse_option=LakehouseOption.sqlite,
            state_option=StateOption.sqlite,
            ACCESS_TOKEN='test_token_for_testing',
        ) as manager:
            yield manager
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def checkpoint_saver(request) -> BaseCheckpointSaver[str]:
    """Create checkpoint saver instance based on --internal flag."""
    if request.config.getoption('--internal'):
        temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(temp_dir.name) / 'test_checkpoint.db'
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        saver = SqliteSaver(conn)

        # Clean up function to close connection and remove temp directory
        def cleanup():
            conn.close()
            temp_dir.cleanup()

        request.addfinalizer(cleanup)
        return saver
    else:
        return AmsdalCheckpointSaver()


@pytest_asyncio.fixture
async def async_checkpoint_saver(request) -> AsyncIterator[BaseCheckpointSaver[str]]:
    """Create checkpoint saver instance for async tests based on --internal flag."""
    if request.config.getoption('--internal'):
        temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(temp_dir.name) / 'test_async_checkpoint.db'
        conn = await aiosqlite.connect(str(db_path))
        saver = AsyncSqliteSaver(conn)

        try:
            yield saver
        finally:
            # Clean up connection and temp directory
            await conn.close()
            temp_dir.cleanup()
    else:
        yield AmsdalCheckpointSaver()


@pytest.fixture
def test_config() -> RunnableConfig:
    """Create test configuration."""
    return {
        'configurable': {
            'thread_id': 'test-thread',
            'checkpoint_ns': 'test-namespace',
        }
    }


@pytest.fixture
def test_checkpoint() -> Checkpoint:
    """Create test checkpoint."""
    return {
        'v': 1,
        'id': str(uuid.uuid4()),
        'ts': '2024-01-01T00:00:00Z',
        'channel_values': {},
        'channel_versions': {},
        'versions_seen': {},
    }


@pytest.fixture
def test_metadata() -> CheckpointMetadata:
    """Create test metadata."""
    return {
        'source': 'input',
        'step': 1,
        'writes': {},
    }


class TestAmsdalCheckpointSaver:
    """Test cases for AmsdalCheckpointSaver."""

    def test_init(self):
        """Test checkpoint saver initialization."""
        saver = AmsdalCheckpointSaver()
        assert saver.jsonplus_serde is not None

    def test_get_tuple_empty(
        self, sync_amsdal_manager: AmsdalManager, checkpoint_saver: AmsdalCheckpointSaver, test_config: RunnableConfig
    ):
        """Test get_tuple when no checkpoint exists."""
        result = checkpoint_saver.get_tuple(test_config)
        assert result is None

    @pytest.mark.asyncio
    async def test_aget_tuple_empty(
        self,
        async_amsdal_manager: AsyncAmsdalManager,
        async_checkpoint_saver: AmsdalCheckpointSaver,
        test_config: RunnableConfig,
    ):
        """Test aget_tuple when no checkpoint exists."""
        result = await async_checkpoint_saver.aget_tuple(test_config)
        assert result is None

    def test_list_empty_config(self, sync_amsdal_manager: AmsdalManager, checkpoint_saver: AmsdalCheckpointSaver):
        """Test list method with None config."""
        result = list(checkpoint_saver.list(None))
        assert result == []

    @pytest.mark.asyncio
    async def test_alist_empty_config(
        self, async_amsdal_manager: AsyncAmsdalManager, async_checkpoint_saver: AmsdalCheckpointSaver
    ):
        """Test alist method with None config."""
        result = []
        async for item in async_checkpoint_saver.alist(None):
            result.append(item)
        assert result == []

    def test_put_and_get(
        self,
        sync_amsdal_manager: AmsdalManager,
        checkpoint_saver: AmsdalCheckpointSaver,
        test_config: RunnableConfig,
        test_checkpoint: Checkpoint,
        test_metadata: CheckpointMetadata,
    ):
        """Test putting and getting a checkpoint."""
        # Put a checkpoint
        new_config = checkpoint_saver.put(
            test_config,
            test_checkpoint,
            test_metadata,
            new_versions={},
        )

        # Verify the config has a checkpoint_id
        assert 'checkpoint_id' in new_config['configurable']

        # Get the checkpoint back
        result = checkpoint_saver.get_tuple(new_config)

        # Verify the checkpoint was saved and retrieved
        assert result is not None
        assert result.checkpoint == test_checkpoint
        assert result.metadata == test_metadata

    @pytest.mark.asyncio
    async def test_aput_and_aget(
        self,
        async_amsdal_manager: AsyncAmsdalManager,
        async_checkpoint_saver: AmsdalCheckpointSaver,
        test_config: RunnableConfig,
        test_checkpoint: Checkpoint,
        test_metadata: CheckpointMetadata,
    ):
        """Test putting and getting a checkpoint asynchronously."""
        # Put a checkpoint
        new_config = await async_checkpoint_saver.aput(
            test_config,
            test_checkpoint,
            test_metadata,
            new_versions={},
        )

        # Verify the config has a checkpoint_id
        assert 'checkpoint_id' in new_config['configurable']

        # Get the checkpoint back
        result = await async_checkpoint_saver.aget_tuple(new_config)

        # Verify the checkpoint was saved and retrieved
        assert result is not None
        assert result.checkpoint == test_checkpoint
        assert result.metadata == test_metadata

    def test_list_with_limit(
        self,
        sync_amsdal_manager: AmsdalManager,
        checkpoint_saver: AmsdalCheckpointSaver,
        test_config: RunnableConfig,
        test_checkpoint: Checkpoint,
        test_metadata: CheckpointMetadata,
    ):
        """Test listing checkpoints with limit."""
        # Put multiple checkpoints
        config1 = checkpoint_saver.put(test_config, test_checkpoint, test_metadata, {})

        checkpoint2 = {**test_checkpoint, 'id': str(uuid.uuid4())}
        config2 = checkpoint_saver.put(config1, checkpoint2, test_metadata, {})

        # List with limit
        checkpoints = list(checkpoint_saver.list(config2, limit=1))

        # Should get only 1 checkpoint
        assert len(checkpoints) == 1

    def test_parent_config_handling(
        self,
        sync_amsdal_manager: AmsdalManager,
        checkpoint_saver: AmsdalCheckpointSaver,
        test_config: RunnableConfig,
        test_checkpoint: Checkpoint,
        test_metadata: CheckpointMetadata,
    ):
        """Test parent config is handled correctly."""
        # Put first checkpoint
        config1 = checkpoint_saver.put(test_config, test_checkpoint, test_metadata, {})

        # Put second checkpoint as child
        checkpoint2 = {**test_checkpoint, 'id': str(uuid.uuid4())}
        config2 = checkpoint_saver.put(config1, checkpoint2, test_metadata, {})

        # Get the child checkpoint
        result = checkpoint_saver.get_tuple(config2)

        # Verify parent config is set
        assert result is not None
        assert result.parent_config is not None
        assert result.parent_config['configurable']['checkpoint_id'] == config1['configurable']['checkpoint_id']
