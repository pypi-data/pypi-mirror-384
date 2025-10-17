Developer Guide
===============

This guide documents the workflows, tooling, and conventions used when extending
or maintaining the Games Collection. It complements ``CONTRIBUTING.md`` by
providing additional context for local development.

Environment setup
-----------------

1. Clone the repository and install the development extras::

       git clone https://github.com/saint2706/Games.git
       cd Games
       pip install -e .[dev]

2. (Optional) Install pre-commit hooks to enforce formatting automatically::

       pre-commit install

Code style checklist
--------------------

* **Python version** – Target Python 3.9+.
* **Formatting** – Run ``black`` with a 160-character line limit::

       black .

* **Imports and linting** – ``ruff check --fix`` handles import ordering and
  surface-level lint rules::

       ruff check --fix .

* **Type hints** – The project expects full type annotations on public
  functions. ``mypy`` is configured in ``pyproject.toml``::

       mypy .

* **Complexity** – Keep cyclomatic complexity at or below 10. The ``radon``
  configuration matches this target::

       radon cc card_games paper_games dice_games logic_games word_games -a -s

Testing
-------

Pytest drives the automated test suite. Run all tests with coverage enabled::

    pytest --cov=card_games --cov=paper_games --cov=dice_games \
           --cov=logic_games --cov=word_games

The ``tests`` directory mirrors the package structure and contains fixtures for
common setups. Add regression tests whenever you introduce new behaviour or fix
bugs.

Documentation workflow
----------------------

The documentation you are reading is built with Sphinx. To regenerate HTML
output locally::

    cd docs
    pip install -r requirements.txt  # once per environment
    make html

The rendered site lives in ``docs/build/html``. Remember to include relevant
updates when you add new features or change user-facing behaviour.

Release checklist
-----------------

* Ensure ``CHANGELOG.md`` captures notable changes.
* Update ``pyproject.toml`` if dependencies or entry points change.
* Verify the launcher scripts defined under ``[project.scripts]`` still point to
  valid modules.
* Tag releases following semantic versioning (``major.minor.patch``).
