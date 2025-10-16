"""App declaration for nautobot_dev_example."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from nautobot.apps import NautobotAppConfig

__version__ = metadata.version(__name__)


class NautobotDevExampleConfig(NautobotAppConfig):
    """App configuration for the nautobot_dev_example app."""

    name = "nautobot_dev_example"
    verbose_name = "Nautobot Dev Example App"
    version = __version__
    author = "Network to Code, LLC"
    description = "Nautobot App to demonstrate how to create a Nautobot App.."
    base_url = "dev-example"
    required_settings = []
    default_settings = {}
    caching_config = {}
    docs_view_name = "plugins:nautobot_dev_example:docs"
    searchable_models = ["devexample"]


config = NautobotDevExampleConfig  # pylint:disable=invalid-name
