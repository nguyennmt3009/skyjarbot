"""
CRUD operations for run history.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from app.data.database import get_connection
from app.data.run_models import RunRecord, StepRecord

_FMT = "%Y-%m-%d %H:%M:%S.%f"


def _ds(dt: Optional[datetime]) -> Optional[str]:
    return dt.strftime(_FMT) if dt else None


def _dt(s: Optional[str]) -> Optional[datetime]:
    return datetime.strptime(s, _FMT) if s else None


# ── Write ─────────────────────────────────────────────────────────────────────

def save_run(run: RunRecord) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO runs "
            "(scenario_id, scenario_name, started_at, finished_at, success, total_steps, steps_done) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                run.scenario_id, run.scenario_name,
                _ds(run.started_at), _ds(run.finished_at),
                int(run.success), run.total_steps, run.steps_done,
            ),
        )
        run_id = cur.lastrowid
        for s in run.steps:
            conn.execute(
                "INSERT INTO run_steps "
                "(run_id, step_index, step_type, description, started_at, finished_at, success, error_msg) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id, s.step_index, s.step_type, s.description,
                    _ds(s.started_at), _ds(s.finished_at),
                    int(s.success), s.error_msg,
                ),
            )
        conn.commit()
    return run_id


# ── Read ──────────────────────────────────────────────────────────────────────

def get_runs(limit: int = 100) -> list[RunRecord]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row_to_run(r) for r in rows]


def get_run_steps(run_id: int) -> list[StepRecord]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM run_steps WHERE run_id = ? ORDER BY step_index", (run_id,)
        ).fetchall()
    return [_row_to_step(r) for r in rows]


def get_scenario_stats(scenario_name: str) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total, "
            "       SUM(success) AS successes, "
            "       AVG(CASE WHEN finished_at IS NOT NULL "
            "           THEN (julianday(finished_at) - julianday(started_at)) * 86400 END) AS avg_duration_s "
            "FROM runs WHERE scenario_name = ?",
            (scenario_name,),
        ).fetchone()
    total = row["total"] or 0
    successes = row["successes"] or 0
    return {
        "total_runs": total,
        "successes": successes,
        "failures": total - successes,
        "success_rate": round(successes / total * 100, 1) if total else 0.0,
        "avg_duration_s": round(row["avg_duration_s"] or 0, 2),
    }


def delete_run(run_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
        conn.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _row_to_run(r) -> RunRecord:
    return RunRecord(
        id=r["id"],
        scenario_id=r["scenario_id"],
        scenario_name=r["scenario_name"],
        started_at=_dt(r["started_at"]),
        finished_at=_dt(r["finished_at"]),
        success=bool(r["success"]),
        total_steps=r["total_steps"],
        steps_done=r["steps_done"],
    )


def _row_to_step(r) -> StepRecord:
    return StepRecord(
        step_index=r["step_index"],
        step_type=r["step_type"],
        description=r["description"],
        started_at=_dt(r["started_at"]),
        finished_at=_dt(r["finished_at"]),
        success=bool(r["success"]),
        error_msg=r["error_msg"],
    )
