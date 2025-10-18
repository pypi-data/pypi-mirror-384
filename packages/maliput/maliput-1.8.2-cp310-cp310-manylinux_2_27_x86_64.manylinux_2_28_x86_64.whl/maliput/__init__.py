import maliput.api as api
import maliput.math as math
import maliput.plugin as plugin

__all__ = [
    'api',
    'math',
    'plugin'
]


def get_maliput_backends():
    import importlib.metadata as importlib_metadata
    entry_points = importlib_metadata.entry_points()
    if 'maliput.backends' in entry_points:
        return entry_points['maliput.backends']
    return []


def update_plugin_path():
    """
    Update MALIPUT_PLUGIN_PATH environment variable with paths
    provided by the `maliput.backends` entry point
    Each backend will have as entry point:
      group: maliput.backends
      name: <backend_name> (e.g. 'maliput_malidrive')
      value: method that returns the path to the location of .so files
    """
    import os

    plugin_paths = []
    for entry_point in get_maliput_backends():
        plugin_paths.append(entry_point.load()())

    plugin_path = os.pathsep.join(plugin_paths)
    if 'MALIPUT_PLUGIN_PATH' in os.environ:
        plugin_path = os.pathsep.join([plugin_path, os.environ['MALIPUT_PLUGIN_PATH']])
    os.environ['MALIPUT_PLUGIN_PATH'] = plugin_path


update_plugin_path()
