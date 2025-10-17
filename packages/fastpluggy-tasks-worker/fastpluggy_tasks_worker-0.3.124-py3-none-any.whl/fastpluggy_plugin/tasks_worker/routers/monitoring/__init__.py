"""
Monitoring router package

This package centralizes operational endpoints intended for monitoring and observability.
It currently provides a placeholder FastAPI router and a migration plan (see plan.md)
for consolidating scattered monitoring-related endpoints into a single, well-structured
namespace.

Scope candidates to (re)host under `/monitoring` include:
- Health probes: readiness, liveness, and component-specific checks
- Metrics exposure: Prometheus scrape endpoints and app metrics
- System insights: CPU/memory/disk, GPU/CUDA info, process/thread pools
- Queue/task scheduler status (e.g., workers, schedules, retries, deadletter)
- Datastore insights: DB connectivity checks, Redis slowlog proxying, cache hit rates

Note: This module is intentionally not auto-registered. Integrators should explicitly
include `router` into the application once the migration plan is executed.
"""
