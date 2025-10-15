from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar, Optional

from sphinx.util.docutils import SphinxDirective

from download_link_replacer.utils import ENV_PROPERTY_NAME


@dataclass
class LinkEntry:
    url: str
    text: Optional[str] = None
    replace_default: bool = False


def _validate_bool(value: Optional[str]) -> bool:
    if value is None:
        return False

    if value.lower() in ("true", "1"):
        return True
    if value.lower() in ("false", "0"):
        return False

    raise ValueError(f"Invalid boolean value: {value}")


class CDLDirective(SphinxDirective):
    required_arguments = 1
    option_spec: ClassVar[dict[str, Callable[[Optional[str]], Any]]] = {
        "replace_default": _validate_bool,
        "text": str,
    }

    def run(self):
        if not hasattr(self.env, ENV_PROPERTY_NAME):
            setattr(self.env, ENV_PROPERTY_NAME, {})

        if self.env.docname not in getattr(self.env, ENV_PROPERTY_NAME):
            getattr(self.env, ENV_PROPERTY_NAME)[self.env.docname] = []

        getattr(self.env, ENV_PROPERTY_NAME)[self.env.docname].append(
            LinkEntry(
                url=self.arguments[0],
                replace_default=self.options.get("replace_default", False),
                text=self.options.get("text", None),
            )
        )

        return []
