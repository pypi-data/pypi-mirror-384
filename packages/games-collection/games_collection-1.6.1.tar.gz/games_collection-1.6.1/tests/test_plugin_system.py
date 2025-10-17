"""Tests for the plugin system."""

import tempfile
from pathlib import Path

from common.architecture import GamePlugin, PluginManager, PluginMetadata


class TestPlugin(GamePlugin):
    """Test plugin implementation."""

    def __init__(self):
        self.initialized = False
        self.shutdown_called = False

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test Author",
            description="A test plugin",
        )

    def initialize(self, **kwargs) -> None:
        self.initialized = True

    def shutdown(self) -> None:
        self.shutdown_called = True

    def get_game_class(self):
        return object


def test_plugin_metadata():
    """Test plugin metadata creation."""
    metadata = PluginMetadata(
        name="test",
        version="1.0",
        author="Author",
        description="Test",
        dependencies=["dep1", "dep2"],
    )

    assert metadata.name == "test"
    assert metadata.version == "1.0"
    assert len(metadata.dependencies) == 2


def test_plugin_manager_initialization():
    """Test plugin manager initialization."""
    manager = PluginManager()
    assert manager is not None


def test_plugin_manager_register_plugin():
    """Test registering a plugin programmatically."""
    manager = PluginManager()
    plugin = TestPlugin()

    # Register plugin directly (simulating what load_plugin does)
    manager._register_plugin("test", plugin)

    assert plugin.initialized
    assert "test" in manager.list_plugins()


def test_plugin_manager_unload():
    """Test unloading a plugin."""
    manager = PluginManager()
    plugin = TestPlugin()

    manager._register_plugin("test", plugin)
    assert "test" in manager.list_plugins()

    manager.unload_plugin("test")
    assert "test" not in manager.list_plugins()
    assert plugin.shutdown_called


def test_plugin_manager_get_plugin():
    """Test getting a loaded plugin."""
    manager = PluginManager()
    plugin = TestPlugin()

    manager._register_plugin("test", plugin)

    retrieved = manager.get_plugin("test")
    assert retrieved is plugin


def test_plugin_manager_get_metadata():
    """Test getting plugin metadata."""
    manager = PluginManager()
    plugin = TestPlugin()

    manager._register_plugin("test", plugin)

    metadata = manager.get_plugin_metadata("test")
    assert metadata is not None
    assert metadata.name == "test_plugin"
    assert metadata.version == "1.0.0"


def test_plugin_manager_discover_plugins():
    """Test discovering plugins from directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = Path(tmpdir)
        manager = PluginManager(plugin_dirs=[plugin_dir])

        # Create a fake plugin file
        plugin_file = plugin_dir / "fake_plugin.py"
        plugin_file.write_text("# Fake plugin")

        discovered = manager.discover_plugins()
        assert "fake_plugin" in discovered


def test_plugin_manager_load_plugin_from_file():
    """Test loading a plugin from a Python file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = Path(tmpdir)
        manager = PluginManager(plugin_dirs=[plugin_dir])

        # Create a real plugin file
        plugin_file = plugin_dir / "real_plugin.py"
        plugin_code = """
from common.architecture import GamePlugin, PluginMetadata

class RealPlugin(GamePlugin):
    def get_metadata(self):
        return PluginMetadata(name="real", version="1.0")

    def initialize(self, **kwargs):
        pass

    def shutdown(self):
        pass

    def get_game_class(self):
        return object

plugin = RealPlugin()
"""
        plugin_file.write_text(plugin_code)

        success = manager.load_plugin("real_plugin")
        assert success
        assert "real_plugin" in manager.list_plugins()


def test_plugin_manager_load_plugin_package_with_relative_import():
    """Test loading a plugin package that uses relative imports."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = Path(tmpdir)
        manager = PluginManager(plugin_dirs=[plugin_dir])

        package_dir = plugin_dir / "relative_plugin"
        package_dir.mkdir()

        init_code = """
from .module import RelativePlugin

plugin = RelativePlugin()
"""
        (package_dir / "__init__.py").write_text(init_code.strip() + "\n")

        module_code = """
from common.architecture import GamePlugin, PluginMetadata


class RelativePlugin(GamePlugin):
    def get_metadata(self):
        return PluginMetadata(name="relative_plugin", version="1.0")

    def initialize(self, **kwargs):
        pass

    def shutdown(self):
        pass

    def get_game_class(self):
        return object
"""
        (package_dir / "module.py").write_text(module_code.strip() + "\n")

        success = manager.load_plugin("relative_plugin")
        assert success
        plugin = manager.get_plugin("relative_plugin")
        assert plugin is not None
        assert plugin.get_metadata().name == "relative_plugin"


def test_plugin_manager_unload_all():
    """Test unloading all plugins."""
    manager = PluginManager()

    plugin1 = TestPlugin()
    plugin2 = TestPlugin()

    manager._register_plugin("plugin1", plugin1)
    manager._register_plugin("plugin2", plugin2)

    assert len(manager.list_plugins()) == 2

    manager.unload_all_plugins()
    assert len(manager.list_plugins()) == 0
    assert plugin1.shutdown_called
    assert plugin2.shutdown_called


def test_plugin_manager_add_directory():
    """Test adding plugin directories."""
    manager = PluginManager()
    new_dir = Path("/tmp/new_plugins")

    manager.add_plugin_directory(new_dir)
    # Check that directory was added (implementation detail, but useful)
    assert new_dir in manager._plugin_dirs
