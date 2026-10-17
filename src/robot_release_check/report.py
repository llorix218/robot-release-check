from __future__ import annotations

from html import escape
from pathlib import Path

from .checks import Finding, overall_status
from .models import Release, TestRecord, latest_qualifying_pass


DISCLAIMER = (
    "This result identifies gaps or mismatches in the supplied evidence. "
    "It does not establish that the physical system was unsafe, untested, or incorrectly deployed."
)


def render_text(release: Release, tests: list[TestRecord], findings: list[Finding]) -> str:
    latest = latest_qualifying_pass(tests, not_after=release.delivered_at)
    lines = [
        "ROBOT RELEASE EVIDENCE REVIEW",
        "",
        f"Delivered Release            {release.release_id}",
        f"Latest Qualifying PASS       {latest.release_id if latest else 'NOT PROVIDED'}",
        "",
    ]
    for f in findings:
        lines.extend([
            f"{f.rule_id}  {f.status}",
            f.title,
            f.summary,
        ])
        lines.extend(f"  - {d}" for d in f.details)
        lines.append("")
    lines.extend(["OVERALL", overall_status(findings), "", DISCLAIMER])
    return "\n".join(lines)


def build_json_report(release: Release, tests: list[TestRecord], findings: list[Finding]) -> dict:
    latest = latest_qualifying_pass(tests, not_after=release.delivered_at)
    return {
        "schema_version": "1",
        "delivered_release": release.release_id,
        "delivered_at": release.delivered_at.isoformat(),
        "latest_qualifying_pass": None if latest is None else {
            "test_id": latest.test_id,
            "release_id": latest.release_id,
            "completed_at": latest.completed_at.isoformat(),
        },
        "overall": overall_status(findings),
        "findings": [
            {
                "rule_id": f.rule_id,
                "title": f.title,
                "severity": f.severity,
                "status": f.status,
                "summary": f.summary,
                "details": list(f.details),
            }
            for f in findings
        ],
        "interpretation_boundary": DISCLAIMER,
    }


def write_html(path: Path, release: Release, tests: list[TestRecord], findings: list[Finding]) -> None:
    latest = latest_qualifying_pass(tests, not_after=release.delivered_at)

    def status_class(status: str) -> str:
        if status == "PASS":
            return "status-pass"
        if status == "EVIDENCE_MISMATCH":
            return "status-critical"
        return "status-gap"

    rows = []
    for f in findings:
        rows.append(
            "<tr>"
            f"<td><code>{escape(f.rule_id)}</code></td>"
            f"<td>{escape(f.title)}</td>"
            f"<td><span class=\"status {status_class(f.status)}\">{escape(f.status)}</span></td>"
            f"<td>{escape(f.summary)}</td>"
            "</tr>"
        )

    detail_sections = []
    for f in findings:
        if f.details:
            items = "".join(f"<li>{escape(d)}</li>" for d in f.details)
            detail_sections.append(
                f"<section class=\"detail\"><h3>{escape(f.rule_id)} — {escape(f.title)}</h3><ul>{items}</ul></section>"
            )

    overall = overall_status(findings)
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>Robot Release Evidence Review</title>
<style>
:root {{ color-scheme: light only; }}
* {{ box-sizing: border-box; }}
html {{ background: #eef1f5 !important; color: #111827 !important; }}
body {{
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  max-width: 1040px;
  margin: 32px auto;
  padding: 36px 40px;
  line-height: 1.55;
  color: #111827 !important;
  background: #ffffff !important;
  border: 1px solid #d9dee7;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(15, 23, 42, 0.08);
  forced-color-adjust: none;
}}
h1, h2, h3, p, li, td, th, strong, span, code {{ opacity: 1 !important; }}
h1 {{ margin: 0 0 6px; font-size: 30px; line-height: 1.2; color: #0f172a !important; }}
h3 {{ margin: 0 0 10px; color: #0f172a !important; }}
.muted {{ margin-top: 0; color: #475569 !important; }}
.summary {{ display:grid; grid-template-columns: repeat(auto-fit,minmax(220px,1fr)); gap:14px; margin:26px 0; }}
.card {{ border:1px solid #cbd5e1; border-radius:12px; padding:17px 18px; background:#f8fafc !important; color:#111827 !important; }}
.card strong {{ display:block; margin-bottom:5px; color:#334155 !important; font-size:13px; text-transform:uppercase; letter-spacing:.04em; }}
.overall {{ font-weight:800; color:#991b1b !important; }}
table {{ width:100%; border-collapse:separate; border-spacing:0; margin:24px 0 30px; border:1px solid #cbd5e1; border-radius:12px; overflow:hidden; background:#ffffff !important; }}
th {{ background:#f1f5f9 !important; color:#1e293b !important; font-size:13px; }}
th,td {{ border-bottom:1px solid #dbe2ea; padding:12px 13px; text-align:left; vertical-align:top; color:#111827 !important; }}
tr:last-child td {{ border-bottom:0; }}
code {{ background:#eef2f7 !important; color:#0f172a !important; padding:2px 6px; border-radius:5px; font-weight:700; }}
.status {{ display:inline-block; padding:4px 8px; border-radius:999px; font-size:12px; line-height:1.25; font-weight:800; white-space:nowrap; border:1px solid transparent; }}
.status-critical {{ background:#fee2e2 !important; color:#991b1b !important; border-color:#fecaca; }}
.status-gap {{ background:#fef3c7 !important; color:#92400e !important; border-color:#fde68a; }}
.status-pass {{ background:#dcfce7 !important; color:#166534 !important; border-color:#bbf7d0; }}
.detail {{ margin: 18px 0; padding: 18px 20px; border:1px solid #dbe2ea; border-radius:12px; background:#ffffff !important; color:#111827 !important; }}
.detail ul {{ margin-bottom:0; }}
.notice {{ margin-top:30px; padding:16px 18px; border-left:5px solid #64748b; background:#f1f5f9 !important; color:#1e293b !important; border-radius:8px; }}
.cta {{ margin-top:20px; padding:18px 20px; border:1px solid #94a3b8; border-radius:12px; background:#f8fafc !important; color:#111827 !important; }}
@media (max-width: 700px) {{
  body {{ margin:0; padding:24px 18px; border-radius:0; border-left:0; border-right:0; }}
  table {{ display:block; overflow-x:auto; }}
}}
@media (prefers-color-scheme: dark) {{
  html {{ background:#eef1f5 !important; color:#111827 !important; }}
  body {{ background:#ffffff !important; color:#111827 !important; }}
}}
</style>
</head>
<body>
<h1>Robot Release Evidence Review</h1>
<p class="muted">Offline evidence-consistency review of the supplied project files.</p>
<div class="summary">
  <div class="card"><strong>Delivered Release</strong>{escape(release.release_id)}</div>
  <div class="card"><strong>Latest Qualifying PASS</strong>{escape(latest.release_id if latest else 'NOT PROVIDED')}</div>
  <div class="card"><strong>Overall</strong><span class="overall">{escape(overall)}</span></div>
</div>
<table>
<thead><tr><th>Rule</th><th>Check</th><th>Result</th><th>Summary</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
{''.join(detail_sections)}
<div class="notice"><strong>Interpretation boundary</strong><br>{escape(DISCLAIMER)}</div>
<div class="cta"><strong>Have a real robot deployment approaching acceptance?</strong><br>Independent evidence review can examine one scoped project using redacted materials, without source-code, production-system, or robot access.</div>
</body></html>"""
    path.write_text(html, encoding="utf-8")
