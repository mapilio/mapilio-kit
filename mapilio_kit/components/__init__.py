"""Mapilio Kit components package.

This package previously eagerly imported ``general_arguments`` and
``edit_config`` from sub-modules. Those re-exports turned out to be unused —
every caller imports directly from the originating module — and they had two
nasty side effects:

* importing any single submodule (e.g.
  ``mapilio_kit.components.utilities.error``) dragged in the entire pipeline
  (ffmpeg wrappers, exiftool helpers, sentry, etc.);
* unit tests that only need lightweight helpers had to stub heavy optional
  dependencies just to import them.

Keeping ``__init__`` empty restores the principle of least surprise. If you
need to expose a public API from this package, prefer explicit ``__all__``
+ PEP 562 lazy imports over top-level imports.
"""
