from __future__ import annotations

from typing import Callable, Iterable, Optional

from fastapi import FastAPI

from svc_infra.cli.cmds.db.sql.alembic_cmds import cmd_setup_and_migrate


def add_data_lifecycle(
    app: FastAPI,
    *,
    auto_migrate: bool = True,
    database_url: str | None = None,
    discover_packages: Optional[list[str]] = None,
    with_payments: bool | None = None,
    on_load_fixtures: Optional[Callable[[], None]] = None,
    retention_jobs: Optional[Iterable[Callable[[], None]]] = None,
    erasure_job: Optional[Callable[[str], None]] = None,
) -> None:
    """
    Wire data lifecycle conveniences:

    - auto_migrate: run end-to-end Alembic setup-and-migrate on startup (idempotent).
    - on_load_fixtures: optional callback to load reference/fixture data once at startup.
    - retention_jobs: optional list of callables to register purge tasks (scheduler integration is external).
    - erasure_job: optional callable to trigger a GDPR erasure workflow for a given principal ID.

    This helper is intentionally minimal: it coordinates existing building blocks
    and offers extension points. Jobs should be scheduled using svc_infra.jobs helpers.
    """

    @app.on_event("startup")
    async def _data_lifecycle_startup() -> None:  # noqa: D401, ANN202
        if auto_migrate:
            # Use existing CLI function to perform end-to-end setup and migrate.
            cmd_setup_and_migrate(
                database_url=database_url,
                overwrite_scaffold=False,
                create_db_if_missing=True,
                create_followup_revision=True,
                initial_message="initial schema",
                followup_message="autogen",
                discover_packages=discover_packages,
                with_payments=with_payments,
            )

        if on_load_fixtures:
            # Run user-provided fixture loader (idempotent expected).
            on_load_fixtures()

    # Store optional jobs on app.state for external schedulers to discover/register.
    if retention_jobs is not None:
        app.state.data_retention_jobs = list(retention_jobs)
    if erasure_job is not None:
        app.state.data_erasure_job = erasure_job


__all__ = ["add_data_lifecycle"]
