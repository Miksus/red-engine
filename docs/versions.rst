
Version history
===============

- ``2.0.1``

    - Fix: ``RedEngine(logger_repo=...)`` now does not remove previous handlers
    - Deprecate: Deprecated ``RedEngine(...).set_logger`` method
    - Docs: Fixed typos in documentation and added docstrings

- ``2.0.0``

    - Update: Completely refactored the interface
    - Remove: Removed a lot of old, poorly supported code

- ``1.2.0``

    - Add: shortcut condition syntax for multiple dependencies
    - Add: new task ``FlaskAPI`` and ``JSONAPI``
    - Add: task dependency view
    - Add: new task ``CodeTask``
    - Add: new hook ``Task.hook_execute``
    - Fix: Bug in ``Return`` if a task executes too quickly
    - Fix: Major bug in optimized task conditions
    - Deprecate: Extensions should no longer be used
    - Update: Now hooks, parsers and task classes are stored in sessions
    - Update: A lot of undocumented code under the hood was removed
    - Update: Removed unsupported templates

- ``1.1.0``

    - Add: conditions ``FuncCond`` and ``TaskCond``
    - Add: new statements to condition syntax
    - Add: new argument ``Return`` and parameter pipelining
    - Add: ``FuncParam``, similar to ``FuncTask`` and ``FuncCond``
    - Fix: Minor bugs
    - Requirements: dropped Pyyaml in hard dependencies
    - Optimization: Now conditions read logs only if cannot be determined without. Can be switched off.

- ``1.0.0``

    - First stable release