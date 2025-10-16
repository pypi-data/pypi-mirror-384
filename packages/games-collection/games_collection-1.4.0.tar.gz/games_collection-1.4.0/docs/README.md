# Documentation

The `docs/` directory contains the Sphinx project for the Games Collection. The
site was rebuilt from scratch to offer a concise, accurate reference for players
and contributors alike.

## Structure

- `source/` – ReStructuredText files that power the documentation.
  - `overview.rst` – project goals and audience.
  - `user_guide.rst` – installation instructions and runtime tips.
  - `developer_guide.rst` – coding standards, testing, and release workflow.
  - `architecture.rst` – explanation of the shared infrastructure.
  - `games_catalog.rst` – authoritative list of included games.
  - `conf.py` – Sphinx configuration.
- `build/` – Generated output (ignored by Git).
- `images/` – Shared assets used by the docs.
- `requirements.txt` – Dependencies needed to build the documentation.

Historic planning notes, migration reports, and workflow audits are still stored
elsewhere in the repository (for example under `docs/status/` and
`docs/planning/`), but they no longer appear in the published Sphinx site.

## Building the site

1. Install the documentation dependencies:

   ```bash
   pip install -r docs/requirements.txt
   ```

1. Build the HTML output:

   ```bash
   cd docs
   make html
   ```

1. Open the generated pages at `docs/build/html/index.html`.

For other formats, run `make latexpdf`, `make epub`, or `make text` from the
same directory.

## Writing new content

- Add new pages inside `docs/source/` and reference them from
  `docs/source/index.rst` (or another toctree) so they appear in navigation.
- Use reStructuredText and follow Sphinx best practices (headings, code blocks,
  cross references).
- Keep examples in sync with the current command-line interfaces and module
  names.
- When describing new games or systems, update both the Sphinx docs and any
  relevant README files in the package directories.
