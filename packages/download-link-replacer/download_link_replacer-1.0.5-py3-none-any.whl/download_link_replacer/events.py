import shutil
from collections.abc import Callable, Iterable
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional
from urllib.parse import urlparse

from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment

from download_link_replacer.directives import LinkEntry
from download_link_replacer.utils import ENV_PROPERTY_NAME, SPHINX_LOGGER

_ALLOWED_REMOTE_SCHEMES = ("https", "http", "ftp")
_OUTPUT_DIR = "_custom_downloads"


class _ReplacementLinkType(Enum):
    REMOTE = 0
    LOCAL = 1


def purge_replacements(_app: Sphinx, env: BuildEnvironment, docname: str):
    SPHINX_LOGGER.debug(f"Purging replacements for {docname}")
    if (
        replacement_dict := getattr(env, ENV_PROPERTY_NAME, None)
    ) is not None and docname in replacement_dict:
        del replacement_dict[docname]


def merge_replacements(
    _app: Sphinx,
    env: BuildEnvironment,
    docnames: Iterable[str],
    other: BuildEnvironment,
):
    SPHINX_LOGGER.debug(f"Merging replacements for {', '.join(docnames)}")

    if (replacement_dict := getattr(env, ENV_PROPERTY_NAME, None)) is None:
        setattr(env, ENV_PROPERTY_NAME, {})
        replacement_dict = getattr(env, ENV_PROPERTY_NAME)

    if (other_dict := getattr(other, ENV_PROPERTY_NAME, None)) is not None:
        replacement_dict.update(other_dict)


def _get_link_type(url: str) -> Optional[_ReplacementLinkType]:
    parsed_res = urlparse(url)

    if parsed_res.scheme in _ALLOWED_REMOTE_SCHEMES:
        return _ReplacementLinkType.REMOTE
    if parsed_res.scheme == "":
        return _ReplacementLinkType.LOCAL

    return None


def _find_download_group(
    entries: list[dict[str, Any]]
) -> Optional[list[dict[str, str]]]:
    for entry in entries:
        if entry["type"] == "group" and entry["label"] == "download-buttons":
            return entry["buttons"]

    return None


def _add_link_to_context(link: LinkEntry, dl_buttons: list[dict[str, str]]):
    # Replace the link in the context
    if link.replace_default:
        # If we are replacing the default button, find it and replace the URL
        for button in dl_buttons:
            if button["type"] == "link" and button["label"] == "download-source-button":
                button["url"] = link.url
                if link.text is not None:
                    button["text"] = link.text
                break
        else:
            SPHINX_LOGGER.warning(
                f"Could not find default download button in {dl_buttons}"
            )
    else:
        # Otherwise, add a new button
        dl_buttons.append(
            {
                "type": "link",
                "url": link.url,
                "text": link.text or link.url.split("/")[-1],
                "tooltip": "Download",
                "icon": "fas fa-file",
                "label": "download-button",
            }
        )


def _process_local_link(
    link: LinkEntry,
    src_dir: Path,
    original_file: Path,
    out_dir: Path,
    pathto: Callable[[str, Literal[1]], str],
) -> str:
    # The path to the file being linked to
    linked_file_path = Path(link.url)
    # If the path is relative, resolve it against the location of
    # the file currently being processed
    if not linked_file_path.is_absolute():
        linked_file_path = (original_file.parent / linked_file_path).resolve(
            strict=True
        )

    # Make sure the path is relative to the source directory
    if not linked_file_path.is_relative_to(src_dir):
        SPHINX_LOGGER.critical(
            f"Replacement link {linked_file_path} is not relative to source directory {src_dir}"
        )
        raise ValueError(
            f"Replacement link {linked_file_path} is not relative to source directory {src_dir}"
        )
    # Verify that the file exists
    if not linked_file_path.exists():
        SPHINX_LOGGER.critical(
            f"Replacement link target ({linked_file_path}) does not exist"
        )
        raise ValueError(f"Replacement link target ({linked_file_path}) does not exist")

    # Compute the target location of the file in the output directory
    copy_target = out_dir / (linked_file_path.relative_to(src_dir))
    # If the file doesn't exist, copy it to the output directory
    if not copy_target.exists():
        SPHINX_LOGGER.debug(
            f"Copied replacement link {linked_file_path} to output directory {copy_target}"
        )
        # Create the parent directory in case it doesn't exist
        copy_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(linked_file_path, copy_target)
    else:
        SPHINX_LOGGER.warning(
            f"Replacement link {link.url} already exists in output directory {copy_target}"
        )

    # Construct the new link
    return f"{pathto(_OUTPUT_DIR, 1)}/{copy_target.relative_to(out_dir)}"


def replace_download_links(
    app: Sphinx, pagename: str, _templatename, context: dict[str, Any], _doctree
):
    if app.builder is None:
        SPHINX_LOGGER.critical("App builder is None")
        raise ValueError("App builder is None")

    env = app.builder.env
    pathto: Callable[[str, Literal[1]], str] = context["pathto"]

    if (
        replacement_dict := getattr(env, ENV_PROPERTY_NAME, None)
    ) is None or pagename not in replacement_dict:
        return

    replacement_links: list[LinkEntry] = replacement_dict[pagename]

    # Find the group of download buttons
    download_group = _find_download_group(context["header_buttons"])
    if download_group is None:
        SPHINX_LOGGER.critical(
            f"Could not find download group in {context['header_buttons']}"
        )
        raise ValueError(
            f"Could not find download group in {context['header_buttons']}"
        )

    src_dir = Path(app.builder.srcdir).resolve(strict=True)
    out_dir = Path(app.builder.outdir) / _OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    # The file currently being processed
    original_file = src_dir / Path(context["sourcename"])

    for link in replacement_links:
        link_type = _get_link_type(link.url)
        if link_type == _ReplacementLinkType.REMOTE:
            new_link = link.url
        elif link_type == _ReplacementLinkType.LOCAL:
            new_link = _process_local_link(
                link=link,
                src_dir=src_dir,
                original_file=original_file,
                out_dir=out_dir,
                pathto=pathto,
            )
        else:
            SPHINX_LOGGER.warning(
                f"Unknown link type: {link.url}. Using it anyway, but no path resolution will be performed."
            )
            new_link = link.url

        link.url = new_link
        _add_link_to_context(link=link, dl_buttons=download_group)
