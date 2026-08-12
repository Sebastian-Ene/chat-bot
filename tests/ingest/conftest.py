"""Ingestion tests.

These cover the ingester, which runs in its own container and is the only part
of the system that touches Docling. Nothing here loads a model: discovery and
state are pure filesystem and Qdrant work, so they stay in the default run.

The Docling-backed tests will need excluding once they exist — they load layout
and table models and take minutes.
"""
