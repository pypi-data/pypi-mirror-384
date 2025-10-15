from importlib.metadata import version
from sphinx.util import logging

VERSION = version("download_link_replacer")

SPHINX_LOGGER = logging.getLogger(__name__)
ENV_PROPERTY_NAME = "download_link_replacements"
