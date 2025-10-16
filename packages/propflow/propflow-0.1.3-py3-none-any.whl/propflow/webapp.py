"""Minimal Flask application exposing PropFlow status endpoints.

This keeps the container alive when run under Gunicorn and provides a
lightweight health check that reports the currently installed version.
"""

from __future__ import annotations

from flask import Flask, jsonify

from ._version import __version__


app = Flask(__name__)


@app.get("/")
def root() -> tuple[str, int]:
    """Return a simple JSON payload confirming the service is running."""

    payload = {"service": "propflow", "status": "ok", "version": __version__}
    return jsonify(payload), 200


@app.get("/healthz")
def health() -> tuple[str, int]:
    """Kubernetes-style liveness/readiness probe endpoint."""

    return jsonify({"status": "ok"}), 200


__all__ = ["app"]
