# Constructed Widget version 1 smoke guide

This fictional guide exists only for local hardware smoke probes.

Widget version 1 listens on port 8123 by default.
The default results page contains 25 items.
Failed requests are retried 3 times.
The default logging level is INFO.
Configuration is read from widget.toml.
The response cache is enabled by default.
Export archives use gzip compression.
The health endpoint is /healthz.
The minimum supported Python version is 3.11.
The authentication token is read from the WIDGET_TOKEN environment variable.
