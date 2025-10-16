Project Overview
================

The Games Collection is an extensible library of traditional games written in
Python 3. The project unifies card, board, dice, logic, and word games behind a
consistent interface so that they can share AI, persistence, and user
experience layers. Every game is packaged as a module that can be imported,
played interactively from the command line, or launched with a graphical user
interface when available.

Core goals
----------

* **Breadth of play** – Ship a curated catalogue of timeless games spanning
  multiple genres while keeping setup friction low.
* **Approachable interfaces** – Provide both terminal-based play and optional
  GUI front ends, letting players choose the experience that fits their
  platform and accessibility needs.
* **Reusable infrastructure** – Encourage contributors to build on shared
  engines, AI strategies, and state management utilities so new games inherit
  existing quality-of-life features.
* **Educational value** – Offer tooling that explains rules, surfaces strategy
  hints, and exposes the algorithms that drive computer opponents.

Key capabilities
----------------

* Modular Python packages that can be executed with ``python -m`` or via
  console entry points installed through ``pip``.
* AI opponents that range from simple heuristics to minimax-based strategies
  depending on the game mechanics.
* Save, load, and replay helpers that live in the ``common`` package and can be
  reused by any title.
* GUI implementations built with Tkinter today, with PyQt-powered upgrades in
  progress for richer visuals and accessibility.
* A structured documentation set (this site!) that explains how to play the
  games, how to extend them, and how to keep contributions aligned with project
  standards.

Audience
--------

The documentation is organised so that players, educators, and developers can
all find targeted material:

* **Players** learn how to install the project and launch their favourite
  games, either against friends or against built-in AI.
* **Educators** can leverage the strategy notes and commentary modes to create
  lesson plans around probability, logic, or game theory.
* **Contributors** receive detailed development guidance, including coding
  standards, architectural principles, and testing workflows.
