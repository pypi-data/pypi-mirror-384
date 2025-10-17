# mkdocs-vwidalias

**mkdocs-vwidalias** is a tiny MkDocs plugin that generates **root-level alias URLs**
based on a page’s front-matter ID.

- Front-matter:
```yaml
  ---
  id: SV-OVERVIEW
  title: Services Overview
  ---
```

* Build output:

```
  site/SV-OVERVIEW/index.html
```
* When opened, it **redirects** to the canonical page (by default appending `#SV-OVERVIEW`):

```
  /path/to/page/#SV-OVERVIEW
```

Now you can share short links like:

```
https://yoursite/SV-OVERVIEW/
```

## Features

* Reads a configurable front-matter field (`id_field`, default `id`)
* Emits alias pages at `/<ID>/index.html` (or `/prefix/<ID>/index.html`)
* Optional `alias_prefix` (e.g., `/id/SV-OVERVIEW/`)
* Optional `#ID` appended to the target (`append_hash: true`)
* Duplicate ID detection (warn or fail)
* Verbose logging for easy debugging

## Install

```bash
pip install mkdocs-vwidalias
```

## Configure (`mkdocs.yml`)

```yaml
plugins:
  - search
  - vwidalias:
      id_field: "id"          # front-matter key
      alias_prefix: ""        # "" => /<ID>/ ; "id" => /id/<ID>/
      append_hash: true       # append '#<ID>' to target URL
      fail_on_duplicate: false
```

## Author pages

```markdown
---
id: SV-OVERVIEW
title: Services Overview
---

# Services Overview
Hello!
```

Build the site and you’ll get:

* Alias: `site/SV-OVERVIEW/index.html`
* Redirect target: `/services/overview/#SV-OVERVIEW` (example)

## Debugging

Run with verbose logs:

```bash
mkdocs build -v
# or
mkdocs serve -v
```

You should see:

```
[mkdocs_vwidalias] Aliases to emit: 1
[mkdocs_vwidalias] Emitted 1 alias pages. Prefix=''
```

## Notes

* Keep `id` values **unique** across pages.
* Works best with MkDocs **pretty URLs** (default).
* Alias pages include a canonical link to the target for SEO.
