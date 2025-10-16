"""Modular snapshot analytics suited for report generation and future tooling."""

from .analyzer import SnapshotAnalyzer, AnalysisReport
from .snapshot_parser import (
    MessageRecord,
    SnapshotRecord,
    load_snapshots,
    parse_snapshots,
    from_engine_snapshot_manager,
)

__all__ = [
    "SnapshotAnalyzer",
    "AnalysisReport",
    "MessageRecord",
    "SnapshotRecord",
    "parse_snapshots",
    "load_snapshots",
    "from_engine_snapshot_manager",
]
