"""Groundtruth Core — the platform spine shared by every product."""

# Version of every persisted artifact shape (traces, scorecards, validation
# reports, CI baselines). Bump only on breaking shape changes; stored CI
# baselines outlive code versions and are the reason this exists (ADR-0005).
SCHEMA_VERSION = 1
