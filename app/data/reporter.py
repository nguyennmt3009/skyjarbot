"""
HTML report generator from run history.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.data.repository import get_runs, get_scenario_stats
from app.data.run_models import RunRecord

_REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"


def generate_html_report(scenario_name: Optional[str] = None, limit: int = 100) -> Path:
    _REPORTS_DIR.mkdir(exist_ok=True)

    runs = get_runs(limit)
    if scenario_name:
        runs = [r for r in runs if r.scenario_name == scenario_name]

    stats = get_scenario_stats(scenario_name) if scenario_name else _overall_stats(runs)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = scenario_name.replace(" ", "_") if scenario_name else "all"
    path = _REPORTS_DIR / f"report_{slug}_{timestamp}.html"
    path.write_text(_build_html(runs, stats, scenario_name), encoding="utf-8")
    return path


# ── HTML builder ──────────────────────────────────────────────────────────────

def _build_html(runs: list[RunRecord], stats: dict, scenario_name: Optional[str]) -> str:
    title = f"SkyjarBot Report — {scenario_name or 'All Scenarios'}"
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    stat_rows = "".join(
        f"<tr><td>{k.replace('_', ' ').title()}</td><td><b>{v}</b></td></tr>"
        for k, v in stats.items()
    )

    run_rows = "".join(_run_row(r) for r in runs)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ font-family: 'Consolas', monospace; padding: 24px; background: #fafafa; color: #222; }}
    h1   {{ font-size: 1.4em; margin-bottom: 4px; }}
    p    {{ color: #666; margin: 0 0 16px; font-size: .85em; }}
    h2   {{ font-size: 1.1em; margin: 20px 0 8px; border-bottom: 1px solid #ddd; padding-bottom: 4px; }}
    table           {{ border-collapse: collapse; width: 100%; margin-bottom: 24px; }}
    th, td          {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left; font-size: .85em; }}
    th              {{ background: #f0f0f0; }}
    tr:nth-child(even) td {{ background: #f9f9f9; }}
    .ok  {{ color: #2a7a2a; font-weight: bold; }}
    .err {{ color: #b00020; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p>Generated: {generated}</p>

  <h2>Summary</h2>
  <table style="width:auto">
    <tr><th>Metric</th><th>Value</th></tr>
    {stat_rows}
  </table>

  <h2>Run History</h2>
  <table>
    <tr>
      <th>#</th><th>Scenario</th><th>Started</th>
      <th>Duration</th><th>Steps</th><th>Status</th>
    </tr>
    {run_rows}
  </table>
</body>
</html>"""


def _run_row(r: RunRecord) -> str:
    status = '<span class="ok">PASS</span>' if r.success else '<span class="err">FAIL</span>'
    started = r.started_at.strftime("%Y-%m-%d %H:%M:%S") if r.started_at else "—"
    duration = f"{r.duration_s:.1f}s" if r.duration_s is not None else "—"
    return (
        f"<tr><td>{r.id}</td><td>{r.scenario_name}</td>"
        f"<td>{started}</td><td>{duration}</td>"
        f"<td>{r.steps_done}/{r.total_steps}</td><td>{status}</td></tr>"
    )


def _overall_stats(runs: list[RunRecord]) -> dict:
    total = len(runs)
    successes = sum(1 for r in runs if r.success)
    durations = [r.duration_s for r in runs if r.duration_s is not None]
    return {
        "total_runs": total,
        "successes": successes,
        "failures": total - successes,
        "success_rate": f"{round(successes / total * 100, 1)}%" if total else "0%",
        "avg_duration_s": f"{round(sum(durations)/len(durations), 2)}s" if durations else "—",
    }
