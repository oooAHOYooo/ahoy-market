#!/usr/bin/env python3
"""Read-only-by-default health checks for the Ahoy web application.

This script deliberately does not load .env files, mutate product source, deploy,
or contact a public URL unless APP_HEALTH_PUBLIC_URL is supplied explicitly.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".local" / "app-health-agent"
REPORTS = LOCAL / "reports"
STATE = LOCAL / "state.json"
DEFAULT_ROUTES = ["/", "/music", "/artists", "/videos", "/podcasts", "/radio", "/events"]


@dataclass
class Check:
    name: str
    status: str  # pass, fail, warn, skip
    detail: str


def run(command: list[str], cwd: Path = ROOT, timeout: int = 900) -> tuple[int, str]:
    try:
        result = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=timeout, check=False)
        return result.returncode, result.stdout[-6000:]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)


def brief(value: str) -> str:
    """Avoid leaking values which look like credentials into a report."""
    lowered = value.lower()
    if any(word in lowered for word in ("secret", "token", "password", "api_key", "authorization")):
        return "Output suppressed because it may contain sensitive configuration."
    return " ".join(value.strip().split())[:700] or "No output."


def git(*args: str) -> tuple[int, str]:
    return run(["git", *args], timeout=60)


def isolated_build(dry_run: bool) -> Check:
    if dry_run:
        return Check("Frontend build", "skip", "Dry run: would build spa/ in an isolated temporary copy.")
    modules = ROOT / "spa" / "node_modules"
    if not modules.is_dir():
        return Check("Frontend build", "skip", "spa/node_modules is absent; install dependencies before a local build check.")
    ignored = shutil.ignore_patterns(".git", ".env", ".env.*", "node_modules", "spa-dist", ".local", "__pycache__", ".pytest_cache")
    with tempfile.TemporaryDirectory(prefix="ahoy-health-build-") as temp:
        snapshot = Path(temp) / "repo"
        shutil.copytree(ROOT, snapshot, ignore=ignored, symlinks=True)
        # Some Capacitor packages are installed at the repository level and are
        # resolved by Node from spa/ via its parent directories.
        (snapshot / "node_modules").symlink_to(ROOT / "node_modules")
        (snapshot / "spa" / "node_modules").symlink_to(modules)
        code, output = run(["npm", "run", "build"], cwd=snapshot / "spa")
        index = snapshot / "spa-dist" / "index.html"
        if code == 0 and index.is_file():
            return Check("Frontend build", "pass", "`npm run build` succeeded in an isolated temporary copy.")
        return Check("Frontend build", "fail", f"`npm run build` failed: {brief(output)}")


def test_checks(dry_run: bool) -> list[Check]:
    if dry_run:
        return [Check("Python tests", "skip", "Dry run: would run pytest."),
                Check("Lint", "skip", "No configured lint script detected.")]
    python = ROOT / ".venv" / "bin" / "python"
    if not python.exists():
        python = Path(sys.executable)
    code, output = run([str(python), "-m", "pytest"], timeout=900)
    if "No module named pytest" in output:
        tests = Check("Python tests", "warn", "pytest is not installed in the selected local Python environment.")
    else:
        tests = Check("Python tests", "pass" if code == 0 else "fail",
                      "pytest passed." if code == 0 else f"pytest failed: {brief(output)}")
    return [tests, Check("Lint", "skip", "No lint command is defined in package.json or spa/package.json.")]


def fetch(url: str) -> tuple[int | None, str]:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "AhoyAppHealthAgent/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, ""
    except urllib.error.HTTPError as exc:
        return exc.code, str(exc)
    except (urllib.error.URLError, ValueError) as exc:
        return None, str(exc)


def public_checks(url: str | None, routes: list[str], dry_run: bool) -> list[Check]:
    if not url:
        return [Check("Public app URL", "skip", "Disabled. Set APP_HEALTH_PUBLIC_URL to enable public-domain checks.")]
    if dry_run:
        return [Check("Public app URL", "skip", f"Dry run: would check {url} and configured routes.")]
    base = url.rstrip("/")
    status, error = fetch(base + "/healthz")
    checks = [Check("Public app URL", "pass" if status and 200 <= status < 400 else "fail",
                    f"GET /healthz returned {status}." if status else f"GET /healthz failed: {brief(error)}")]
    for route in routes:
        status, error = fetch(base + route)
        checks.append(Check(f"Public route {route}", "pass" if status and 200 <= status < 400 else "fail",
                            f"HTTP {status}." if status else brief(error)))
    return checks


def browser_qa(routes: list[str], dry_run: bool) -> Check:
    """Run the repo-local Playwright check only when explicitly requested."""
    if dry_run:
        return Check("Browser QA", "skip", "Dry run: would preview spa-dist and inspect desktop/mobile routes.")
    if not (ROOT / "spa-dist" / "index.html").is_file():
        return Check("Browser QA", "skip", "spa-dist/index.html is absent; run a frontend build before browser QA.")
    script = ROOT / "tools" / "app-health-agent" / "browser-qa.mjs"
    output_dir = REPORTS / (datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ") + "-screenshots")
    code, output = run(["node", str(script), str(output_dir), json.dumps(routes)], timeout=180)
    if code == 0:
        return Check("Browser QA", "pass", f"Desktop/mobile rendered QA passed; screenshots: `{output_dir.relative_to(ROOT)}`.")
    if "Executable doesn't exist" in output:
        return Check("Browser QA", "warn", "Playwright is installed but its Chromium browser is not installed locally.")
    return Check("Browser QA", "fail", f"Browser QA failed: {brief(output)}")


def git_summary() -> tuple[str, list[str]]:
    _, branch = git("branch", "--show-current")
    _, status = git("status", "--short")
    _, main_delta = git("diff", "--stat", "main...HEAD")
    previous = {}
    if STATE.exists():
        try:
            previous = json.loads(STATE.read_text())
        except json.JSONDecodeError:
            previous = {}
    _, head = git("rev-parse", "HEAD")
    prior_head = previous.get("head")
    since_last = "First run; no prior baseline."
    if prior_head:
        code, diff = git("diff", "--stat", f"{prior_head}..HEAD")
        since_last = diff.strip() if code == 0 and diff.strip() else "No committed changes since the prior run."
    status_lines = status.strip().splitlines()
    status_excerpt = "\n".join(status_lines[:20]) or "clean"
    if len(status_lines) > 20:
        status_excerpt += f"\n... {len(status_lines) - 20} additional entries omitted"
    return textwrap.dedent(f"""\
        Branch: `{branch.strip() or 'detached'}`

        Working tree:
        ```text
        {status_excerpt}
        ```

        Committed delta from `main`:
        ```text
        {main_delta.strip() or 'none'}
        ```

        Since the previous health run:
        ```text
        {since_last}
        ```"""), [head.strip(), branch.strip()]


def severity(checks: list[Check]) -> list[str]:
    issues = []
    for item in checks:
        if item.status == "fail":
            issues.append(f"- **High — {item.name}:** {item.detail}")
        elif item.status == "warn":
            issues.append(f"- **Medium — {item.name}:** {item.detail}")
    if not issues:
        issues.append("- **Info:** No failing checks in this run. Skipped checks still need explicit configuration or dependencies.")
    return issues


def write_report(checks: list[Check], git_block: str, dry_run: bool) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    lines = ["# App Health Report", "", f"Generated: `{stamp}`", f"Mode: `{'dry-run' if dry_run else 'read-only'}`", "",
             "## Checks", "", "| Check | Result | Detail |", "| --- | --- | --- |"]
    lines += [f"| {check.name} | {check.status.upper()} | {check.detail} |" for check in checks]
    lines += ["", "## Git", "", git_block, "", "## Needs attention", "", *severity(checks), ""]
    path = REPORTS / f"{stamp}.md"
    path.write_text("\n".join(lines))
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only health checks for app.ahoy.ooo")
    parser.add_argument("--dry-run", action="store_true", help="Discover checks without executing builds, tests, or HTTP requests.")
    parser.add_argument("--routes", default=os.getenv("APP_HEALTH_ROUTES", ",".join(DEFAULT_ROUTES)),
                        help="Comma-separated public SPA routes; only used when APP_HEALTH_PUBLIC_URL is set.")
    parser.add_argument("--browser", action="store_true", help="Opt in to local desktop/mobile browser QA against the existing spa-dist build.")
    args = parser.parse_args()
    routes = [route.strip() for route in args.routes.split(",") if route.strip().startswith("/")]
    checks = [isolated_build(args.dry_run), *test_checks(args.dry_run)]
    checks.extend(public_checks(os.getenv("APP_HEALTH_PUBLIC_URL"), routes, args.dry_run))
    checks.append(browser_qa(routes, args.dry_run) if args.browser else
                  Check("Browser QA", "skip", "Disabled. Re-run with --browser to inspect the local rendered SPA."))
    git_block, state = git_summary()
    report = write_report(checks, git_block, args.dry_run)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"head": state[0], "branch": state[1], "ran_at": datetime.now(timezone.utc).isoformat()}, indent=2))
    print(report)
    return 1 if any(check.status == "fail" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
