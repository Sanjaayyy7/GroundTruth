# Security Policy

## Scope

Groundtruth is an **offline** evaluation harness. It runs no network
service, collects no telemetry, and makes no outbound calls except to a
local Ollama server when a real-model subject is explicitly requested
(`--agent ollama:<model>`). Scenario files and recorded traces contain
adversarial strings (prompt injections, fake secrets) **by design**; the
HTML report escapes them before rendering.

Things that are *not* vulnerabilities here: the bundled attack scenarios
themselves, the deliberately vulnerable demo agents, or fake credentials
inside `scenarios/` and `validation/` — they are the test corpus.

## Reporting a vulnerability

If you find a real security issue — e.g. unescaped adversarial content
reaching the report, path traversal via scenario or trace files, or
anything that executes untrusted content — please report it privately:

- GitHub: private vulnerability reporting on this repository, or
- Email: sanmanivas@ucdavis.edu

Include reproduction steps. You can expect an acknowledgement within
7 days. Please do not open a public issue for an unpatched vulnerability.

## Supported versions

| Version | Supported |
|---|---|
| v0.8.x (latest tag) | yes |
| earlier milestones | no — historical record |
