"""
Custom Pytest Plugin for Jira-Style Defect Classification (P1-P4 Severity).
Collects test execution metrics and generates a rich HTML & Markdown Defect Report.
"""
import os
import time
from datetime import datetime, timezone
import pytest


class JiraDefectReporter:
    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.time()

    def record_result(self, item, report):
        if report.when != "call" and not (report.when == "setup" and report.skipped):
            return

        # Extract Jira marker
        jira_marker = item.get_closest_marker("jira")
        severity = "P3 - Major"
        ticket = "QA-AUTO"

        if jira_marker:
            ticket = jira_marker.kwargs.get("ticket") or (jira_marker.args[0] if jira_marker.args else "QA-AUTO")
            sev_arg = jira_marker.kwargs.get("severity") or (jira_marker.args[1] if len(jira_marker.args) > 1 else "P3")
            sev_map = {
                "P1": "P1 - Blocker",
                "P2": "P2 - Critical",
                "P3": "P3 - Major",
                "P4": "P4 - Minor",
            }
            severity = sev_map.get(sev_arg.upper(), sev_arg)
        elif item.get_closest_marker("p1_blocker"):
            severity = "P1 - Blocker"
        elif item.get_closest_marker("p2_critical"):
            severity = "P2 - Critical"
        elif item.get_closest_marker("p3_major"):
            severity = "P3 - Major"
        elif item.get_closest_marker("p4_minor"):
            severity = "P4 - Minor"

        error_message = ""
        if report.failed:
            error_message = str(report.longrepr)

        self.results.append({
            "nodeid": item.nodeid,
            "name": item.name,
            "module": item.module.__name__ if hasattr(item, "module") else "",
            "ticket": ticket,
            "severity": severity,
            "status": "PASSED" if report.passed else ("FAILED" if report.failed else "SKIPPED"),
            "duration": round(report.duration * 1000, 2),
            "error": error_message,
        })

    def generate_reports(self):
        self.end_time = time.time()
        total_time = round(self.end_time - self.start_time, 2)
        os.makedirs("reports", exist_ok=True)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASSED")
        failed = sum(1 for r in self.results if r["status"] == "FAILED")
        skipped = sum(1 for r in self.results if r["status"] == "SKIPPED")

        p1_total = sum(1 for r in self.results if "P1" in r["severity"])
        p1_pass = sum(1 for r in self.results if "P1" in r["severity"] and r["status"] == "PASSED")

        p2_total = sum(1 for r in self.results if "P2" in r["severity"])
        p2_pass = sum(1 for r in self.results if "P2" in r["severity"] and r["status"] == "PASSED")

        p3_total = sum(1 for r in self.results if "P3" in r["severity"])
        p3_pass = sum(1 for r in self.results if "P3" in r["severity"] and r["status"] == "PASSED")

        p4_total = sum(1 for r in self.results if "P4" in r["severity"])
        p4_pass = sum(1 for r in self.results if "P4" in r["severity"] and r["status"] == "PASSED")

        pass_rate = round((passed / total * 100), 1) if total > 0 else 0

        # Generate HTML Report
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Jira Defect Severity Test Execution Report</title>
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: #111827;
      --border: #1f2937;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --p1: #ef4444;
      --p2: #f59e0b;
      --p3: #8b5cf6;
      --p4: #3b82f6;
      --success: #10b981;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    body {{ background: var(--bg); color: var(--text); padding: 32px 24px; min-height: 100vh; }}
    .header {{ margin-bottom: 24px; border-bottom: 1px solid var(--border); padding-bottom: 16px; display: flex; justify-content: space-between; align-items: flex-end; }}
    .header h1 {{ font-size: 24px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 8px; }}
    .header p {{ color: var(--text-muted); font-size: 13px; margin-top: 4px; }}
    .timestamp {{ font-size: 12px; color: var(--text-muted); }}
    
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }}
    .kpi-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }}
    .kpi-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); font-weight: 600; margin-bottom: 6px; }}
    .kpi-val {{ font-size: 24px; font-weight: 700; }}
    .kpi-sub {{ font-size: 12px; margin-top: 4px; }}

    .p1-card {{ border-left: 4px solid var(--p1); }}
    .p2-card {{ border-left: 4px solid var(--p2); }}
    .p3-card {{ border-left: 4px solid var(--p3); }}
    .p4-card {{ border-left: 4px solid var(--p4); }}
    .total-card {{ border-left: 4px solid var(--success); }}

    .table-container {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }}
    th {{ background: #162032; padding: 12px 16px; color: var(--text-muted); font-weight: 600; border-bottom: 1px solid var(--border); }}
    td {{ padding: 12px 16px; border-bottom: 1px solid #1c2638; vertical-align: middle; }}
    tr:hover {{ background: #151f30; }}
    
    .badge {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
    .badge-p1 {{ background: rgba(239, 68, 68, 0.15); color: #fca5a5; border: 1px solid #ef4444; }}
    .badge-p2 {{ background: rgba(245, 158, 11, 0.15); color: #fcd34d; border: 1px solid #f59e0b; }}
    .badge-p3 {{ background: rgba(139, 92, 246, 0.15); color: #d8b4fe; border: 1px solid #8b5cf6; }}
    .badge-p4 {{ background: rgba(59, 130, 246, 0.15); color: #93c5fd; border: 1px solid #3b82f6; }}
    
    .status-pass {{ color: #34d399; font-weight: 600; }}
    .status-fail {{ color: #f87171; font-weight: 600; }}
    .ticket {{ font-family: monospace; font-size: 12px; color: #60a5fa; }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1>⚡ REST & GraphQL Test Execution Report</h1>
      <p>Data-Driven Quality Audit with Jira Defect Severity Classification (P1–P4)</p>
    </div>
    <div class="timestamp">
      Executed: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")} | Runtime: {total_time}s
    </div>
  </div>

  <div class="grid">
    <div class="kpi-card total-card">
      <div class="kpi-title">Total Tests & Pass Rate</div>
      <div class="kpi-val" style="color: var(--success);">{passed}/{total} ({pass_rate}%)</div>
      <div class="kpi-sub" style="color: var(--text-muted);">{failed} Failed | {skipped} Skipped</div>
    </div>
    <div class="kpi-card p1-card">
      <div class="kpi-title">P1 - Blocker</div>
      <div class="kpi-val" style="color: var(--p1);">{p1_pass}/{p1_total}</div>
      <div class="kpi-sub" style="color: var(--text-muted);">Auth / Security / ACID</div>
    </div>
    <div class="kpi-card p2-card">
      <div class="kpi-title">P2 - Critical</div>
      <div class="kpi-val" style="color: var(--p2);">{p2_pass}/{p2_total}</div>
      <div class="kpi-sub" style="color: var(--text-muted);">Core CRUD / Orders</div>
    </div>
    <div class="kpi-card p3-card">
      <div class="kpi-title">P3 - Major</div>
      <div class="kpi-val" style="color: var(--p3);">{p3_pass}/{p3_total}</div>
      <div class="kpi-sub" style="color: var(--text-muted);">Filters / Search / GraphQL</div>
    </div>
    <div class="kpi-card p4-card">
      <div class="kpi-title">P4 - Minor</div>
      <div class="kpi-val" style="color: var(--p4);">{p4_pass}/{p4_total}</div>
      <div class="kpi-sub" style="color: var(--text-muted);">Validation & Boundary Edge</div>
    </div>
  </div>

  <div class="table-container">
    <table>
      <thead>
        <tr>
          <th>Jira Ticket</th>
          <th>Severity</th>
          <th>Test Identifier</th>
          <th>Module</th>
          <th>Duration</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
"""
        for r in self.results:
            sev_class = "badge-p3"
            if "P1" in r["severity"]:
                sev_class = "badge-p1"
            elif "P2" in r["severity"]:
                sev_class = "badge-p2"
            elif "P4" in r["severity"]:
                sev_class = "badge-p4"

            status_class = "status-pass" if r["status"] == "PASSED" else "status-fail"
            html_content += f"""
        <tr>
          <td><span class="ticket">{r["ticket"]}</span></td>
          <td><span class="badge {sev_class}">{r["severity"]}</span></td>
          <td><strong>{r["name"]}</strong></td>
          <td><span style="color: var(--text-muted);">{r["module"]}</span></td>
          <td>{r["duration"]}ms</td>
          <td><span class="{status_class}">● {r["status"]}</span></td>
        </tr>
"""
        html_content += """
      </tbody>
    </table>
  </div>
</body>
</html>
"""
        with open("reports/jira_defect_report.html", "w") as f:
            f.write(html_content)

        # Markdown Report
        md_content = f"""# 📊 Jira Defect Severity Test Report

- **Date**: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
- **Total Tests**: {total}
- **Pass Rate**: {pass_rate}% ({passed} Passed, {failed} Failed)
- **Execution Time**: {total_time}s

| Severity Tier | Tests | Passed | Pass Rate |
| :--- | :--- | :--- | :--- |
| **P1 - Blocker** | {p1_total} | {p1_pass} | {round(p1_pass/p1_total*100 if p1_total else 100, 1)}% |
| **P2 - Critical** | {p2_total} | {p2_pass} | {round(p2_pass/p2_total*100 if p2_total else 100, 1)}% |
| **P3 - Major** | {p3_total} | {p3_pass} | {round(p3_pass/p3_total*100 if p3_total else 100, 1)}% |
| **P4 - Minor** | {p4_total} | {p4_pass} | {round(p4_pass/p4_total*100 if p4_total else 100, 1)}% |
"""
        with open("reports/jira_defect_summary.md", "w") as f:
            f.write(md_content)


reporter = JiraDefectReporter()


def pytest_configure(config):
    config.addinivalue_line("markers", "jira(ticket, severity): Jira defect tracker marker")
    config.addinivalue_line("markers", "p1_blocker: Critical P1 blocker severity")
    config.addinivalue_line("markers", "p2_critical: High P2 critical severity")
    config.addinivalue_line("markers", "p3_major: Medium P3 major severity")
    config.addinivalue_line("markers", "p4_minor: Low P4 minor severity")
    config.addinivalue_line("markers", "rest: REST API test cases")
    config.addinivalue_line("markers", "graphql: GraphQL API test cases")
    reporter.start()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    reporter.record_result(item, report)


def pytest_sessionfinish(session, exitstatus):
    reporter.generate_reports()
