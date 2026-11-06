"""AI-A04 final project acceptance validation."""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.adapters.db import get_connection


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

checks = {}


def record(name, passed, detail):
    checks[name] = {
        "passed": bool(passed),
        "detail": detail,
    }
    print(f"{'PASS' if passed else 'FAIL'}: {name} — {detail}")


print("=== AI-A04 Final Acceptance Validation ===")

# 1. Regression tests
tests = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-q"],
    cwd=ROOT,
    capture_output=True,
    text=True,
)

summary = tests.stdout.strip().splitlines()
last_line = summary[-1] if summary else tests.stderr[-300:]

record(
    "Automated regression suite",
    tests.returncode == 0,
    last_line,
)

# 2. MCP assessment demonstration and correlated events
demo = subprocess.run(
    [sys.executable, "-m", "src.agents.demo"],
    cwd=ROOT,
    capture_output=True,
    text=True,
)

events = []

for line in demo.stderr.splitlines():
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        continue
    if "trace_id" in event:
        events.append(event)

correlated = (
    len(events) == 8
    and len({e["trace_id"] for e in events}) == 1
    and len({e["assessment_id"] for e in events}) == 1
)

record(
    "Enterprise assessment",
    demo.returncode == 0
    and "PASS: Enterprise assessment agent" in demo.stdout,
    "ACME demonstration completed" if demo.returncode == 0
    else "Demo execution failed",
)

record(
    "Execution correlation",
    correlated,
    f"{len(events)} structured client-side events",
)

# 3. Database identity and read-only defaults
try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    current_user AS db_role,
                    current_setting(
                        'default_transaction_read_only'
                    ) AS read_only
                """
            )
            configuration = cur.fetchone()

    db_ok = (
        configuration["db_role"] == "a04_reader"
        and configuration["read_only"] == "on"
    )
    detail = (
        f"role={configuration['db_role']}, "
        f"read_only={configuration['read_only']}"
    )
except Exception as exc:
    db_ok = False
    detail = type(exc).__name__

record("Database security configuration", db_ok, detail)

# 4. Existing measured performance evidence
benchmark_path = RESULTS / "day4_benchmark.json"

try:
    benchmark = json.loads(benchmark_path.read_text())
    benchmark_ok = (
        benchmark["measured_runs"] == 10
        and len(benchmark["runs"]) == 10
        and all(
            key in benchmark["summary"]
            for key in (
                "assessment_ms",
                "startup_ms",
                "discovery_ms",
                "tool_total_ms",
            )
        )
    )
    detail = (
        f"{benchmark['measured_runs']} measured runs, "
        f"median assessment "
        f"{benchmark['summary']['assessment_ms']['median_ms']:.2f} ms"
    )
except (OSError, KeyError, ValueError) as exc:
    benchmark_ok = False
    detail = type(exc).__name__

record("Performance benchmark", benchmark_ok, detail)

# 5. Final record
passed = all(item["passed"] for item in checks.values())

report = {
    "project": "AI-A04",
    "validation_date": datetime.now(timezone.utc).isoformat(),
    "overall_passed": passed,
    "checks": checks,
}

output = RESULTS / "day4_acceptance.json"
output.write_text(json.dumps(report, indent=2) + "\n")

print()
print(f"Acceptance: {sum(c['passed'] for c in checks.values())}"
      f"/{len(checks)} checks passed")
print(f"Saved: {output}")

sys.exit(0 if passed else 1)
