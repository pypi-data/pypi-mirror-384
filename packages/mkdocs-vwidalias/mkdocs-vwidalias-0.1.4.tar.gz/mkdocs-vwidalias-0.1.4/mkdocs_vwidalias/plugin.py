# mkdocs_vwidalias/plugin.py
from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Dict, Optional

from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.pages import Page
from mkdocs.utils import write_file
import logging

log = logging.getLogger("mkdocs.plugins.vwidalias")

# HTML id: must start with a letter, then [A-Za-z0-9_ - : .]
VALID_HTML_ID = re.compile(r"^[A-Za-z][\w\-\:\.]*$")

def normalize_id(raw: str) -> Optional[str]:
    if not raw:
        return None
    raw = str(raw).strip()
    raw = re.sub(r"\s+", "-", raw)  # spaces -> hyphens
    return raw if VALID_HTML_ID.match(raw) else None

REDIRECT_TEMPLATE = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Redirecting…</title>
    <meta http-equiv="refresh" content="0; url=/{target}">
    <link rel="canonical" href="/{target}">
    <script>location.replace("/{target}");</script>
    <style>body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;padding:2rem}}</style>
  </head>
  <body>
    <p>Redirecting to <a href="/{target}">/{target}</a>…</p>
  </body>
</html>
"""

class VwidAliasPlugin(BasePlugin):
    """
    vwidalias:
    Create alias pages at /<ID>/index.html (or /<prefix>/<ID>/index.html) that
    redirect to the page containing that ID (optionally appending '#<ID>').
    The ID is read from front-matter (default key: 'id').
    """

    config_scheme = (
        ("id_field", config_options.Type(str, default="id")),
        ("alias_prefix", config_options.Type(str, default="")),     # e.g. "id" -> /id/<ID>/
        ("append_hash", config_options.Type(bool, default=True)),   # append '#<ID>' to target
        ("fail_on_duplicate", config_options.Type(bool, default=False)),
    )

    def __init__(self):
        super().__init__()
        self._site_dir: Optional[str] = None
        self._map: Dict[str, str] = {}     # id -> target url (without leading '/')
        self._source: Dict[str, str] = {}  # id -> src path (for logs)

    def on_config(self, config: MkDocsConfig, **kwargs):
        self._site_dir = config.site_dir
        return config

    def on_page_markdown(self, markdown: str, page: Page, config: MkDocsConfig, files, **kwargs):
        # page.meta is available here
        id_field = self.config["id_field"]
        raw_id = (page.meta or {}).get(id_field)
        html_id = normalize_id(raw_id) if raw_id else None
        if not html_id:
            return markdown

        # Respect MkDocs' URL style configuration
        use_directory_urls = getattr(config, "use_directory_urls", True)

        page_url = page.url or ""
        if use_directory_urls:
            if page_url.endswith("index.html"):
                page_url = page_url[:-10]
            if page_url.endswith(".html"):
                page_url = page_url[:-5]
            if page_url and not page_url.endswith("/"):
                page_url += "/"
        else:
            if page_url.endswith("/"):
                page_url = page_url[:-1]
            if not page_url.endswith(".html"):
                if page_url:
                    page_url = f"{page_url}.html"
                else:
                    page_url = "index.html"

        # Compose target respecting append_hash
        if self.config.get("append_hash", True):
            target = f"{page_url}#{html_id}"
        else:
            target = page_url

        # Handle duplicates (per config)
        if html_id in self._map:
            msg = f"[vwidalias] Duplicate id '{html_id}' on: {self._source[html_id]} AND {page.file.src_path}"
            if self.config.get("fail_on_duplicate", False):
                raise ValueError(msg)
            else:
                log.warning(msg)
                # keep the first discovered mapping; skip the new one
                return markdown

        self._map[html_id] = target
        self._source[html_id] = page.file.src_path
        log.debug("[vwidalias] found id=%s on %s -> %s", html_id, page.file.src_path, target)
        return markdown

    def on_post_build(self, config: MkDocsConfig, **kwargs):
        if not self._map:
            log.info("[vwidalias] no IDs discovered")
            return

        prefix = (self.config["alias_prefix"] or "").strip("/")

        for html_id, target in self._map.items():
            parts = [p for p in (prefix, html_id) if p]
            alias_dir = os.path.join(self._site_dir, *parts)
            Path(alias_dir).mkdir(parents=True, exist_ok=True)
            alias_index = os.path.join(alias_dir, "index.html")

            html = REDIRECT_TEMPLATE.format(target=target)
            write_file(html.encode("utf-8"), alias_index)

            log.debug("[vwidalias] wrote alias: /%s -> /%s", "/".join(parts), target)
