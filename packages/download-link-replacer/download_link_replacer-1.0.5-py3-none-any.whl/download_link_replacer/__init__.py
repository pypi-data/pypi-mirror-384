from sphinx.application import Sphinx

from download_link_replacer.directives import CDLDirective
from download_link_replacer.events import (
    merge_replacements,
    purge_replacements,
    replace_download_links,
)
from download_link_replacer.utils import VERSION

__version__ = VERSION

# Make sure we run *after* the theme hooks
_PRIORITY = 502


def setup(app: Sphinx):
    app.add_directive("custom_download_link", CDLDirective)

    app.connect("env-merge-info", merge_replacements)
    app.connect("env-purge-doc", purge_replacements)
    app.connect("html-page-context", replace_download_links, priority=_PRIORITY)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
