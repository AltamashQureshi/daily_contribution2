"""
╔══════════════════════════════════════════════════════╗
║        GitHub Activity Graph Enhancer v2.0           ║
║  Commits · Issues · Pull Requests · Realistic Bursts ║
╚══════════════════════════════════════════════════════╝

Setup:
  pip install requests
  Run inside a cloned GitHub repo directory.

Fill in the CONFIG section below before running.
"""

import os
import sys
import time
import random
import subprocess
import requests
from datetime import datetime, timedelta

# ================================================================
#  CONFIG  ← edit this section
# ================================================================

START_DATE        = datetime(2020, 1, 5)
END_DATE          = datetime.today()

GIT_EMAIL         = "your-email@example.com"       # Email linked to your GitHub account
GIT_NAME          = "your-github-username"          # Your GitHub display name
GITHUB_TOKEN      = "YOUR_PAT_HERE"                 # ghp_xxxxxxxxxxxx  (needs repo scope)
GITHUB_USERNAME   = "your-github-username"          # Your GitHub username
GITHUB_REPO       = "your-repo-name"                # Full URL or just repo name e.g. "my-repo"

BRANCH            = "main"
LOG_FILE          = "activity.log"

# ── Commit volume ───────────────────────────────────────────────
COMMIT_WEIGHTS = {
    0:  15,
    1:   8,
    2:  12,
    3:  14,
    4:  13,
    5:  12,
    6:   9,
    7:   7,
    8:   5,
    9:   4,
    10:  3,
    11:  2,
    12:  2,
    13:  1,
    14:  1,
    15:  1,
    16:  1,
    17:  1,
    18:  1,
}

# ── Burst streaks ───────────────────────────────────────────────
BURST_WEEK_PROBABILITY = 0.08
BURST_BONUS_MIN        = 4
BURST_BONUS_MAX        = 8

# ── Issues / PRs ────────────────────────────────────────────────
AVG_ISSUES_PER_WEEK = 4
AVG_PRS_PER_WEEK    = 3

# ── Reliability ─────────────────────────────────────────────────
API_MAX_RETRIES   = 4
API_RETRY_DELAY   = 6
PUSH_BATCH_SIZE   = 150

# ── Resume support ──────────────────────────────────────────────
CHECKPOINT_FILE   = ".activity_checkpoint"

# ================================================================
#  VOCABULARY
# ================================================================

ACTIONS = [
    "fix", "feat", "refactor", "improve", "add", "remove",
    "optimize", "cleanup", "tweak", "adjust", "enhance", "resolve",
    "implement", "restructure", "document", "migrate", "test",
    "revert", "bump", "patch", "style", "perf", "ci", "chore",
]

SCOPES = [
    "logging", "tracker", "report", "sync", "api", "generator",
    "writer", "parser", "scheduler", "timestamps", "workflow",
    "pipeline", "auth", "cache", "db", "ui", "config", "tests",
    "docs", "ci", "deps", "build", "core", "utils", "types",
]

DETAILS = [
    "edge cases in date handling",
    "performance under high load",
    "randomization logic",
    "output formatting",
    "error handling and retries",
    "data consistency checks",
    "logging format to JSON",
    "file writer buffer flush",
    "commit workflow ordering",
    "retry logic with backoff",
    "null pointer guard",
    "memory leak on large datasets",
    "timezone offset calculation",
    "config validation on startup",
    "unused variable warnings",
    "type hints across module",
    "deprecation warnings",
    "docstring accuracy",
    "test coverage for edge paths",
    "linting issues",
    "CI pipeline speed",
    "startup time",
    "duplicate log entries",
    "missing unit tests",
    "code duplication in helpers",
]

ISSUE_TITLES = [
    "bug: incorrect timestamp on midnight commits",
    "feat: add retry logic for failed API calls",
    "chore: clean up unused imports",
    "enhancement: improve logging verbosity",
    "bug: data sync fails on empty payload",
    "feat: support multiple branches",
    "chore: update dependencies to latest",
    "bug: race condition in scheduler",
    "enhancement: add dry-run mode",
    "feat: configurable commit frequency",
    "bug: file writer skips last record",
    "chore: add unit tests for parser",
    "enhancement: better error messages in CLI",
    "feat: webhook support for CI triggers",
    "bug: date range off by one day",
    "feat: add progress bar to long-running ops",
    "bug: auth token not refreshed on expiry",
    "enhancement: parallelize API calls",
    "chore: remove dead code in utils",
    "feat: add --verbose flag",
    "bug: config file not found on Windows paths",
    "enhancement: cache frequently used API responses",
    "chore: migrate from setup.py to pyproject.toml",
    "feat: structured output as JSON or CSV",
    "bug: memory grows unbounded on large repos",
]

ISSUE_BODIES = [
    "Noticed this on a fresh repo. Steps to reproduce: run with default config and observe output.",
    "This would improve usability for larger teams. Open to suggestions on the best approach.",
    "Minor cleanup to keep the codebase tidy. No functional changes expected.",
    "Current plain-text output is hard to parse in CI. Proposing JSON logging.",
    "Happens intermittently under load. Added a minimal reproduction case below.",
    "Targeting feature branches would produce more realistic contribution graphs.",
    "Several packages have security patches pending — running `pip-audit` reveals 3 issues.",
    "Observed when two jobs fire within the same millisecond window.",
    "Allow previewing what would happen without writing anything to disk or remote.",
    "Hard-coding the frequency makes automated testing unnecessarily fragile.",
    "Confirmed on Python 3.10 and 3.11. Not reproduced on 3.9.",
    "The fix is straightforward — happy to submit a PR if assigned.",
    "Related to the discussion in #12. Leaving this open for further input.",
]

PR_TITLES = [
    "fix: resolve timestamp edge case at midnight",
    "feat: add configurable commit frequency via config file",
    "chore: remove deprecated helper functions",
    "refactor: split large main() into focused sub-functions",
    "fix: handle empty payload in data sync gracefully",
    "feat: implement --dry-run flag",
    "docs: update README with full usage examples",
    "fix: correct off-by-one in date range loop",
    "feat: add retry logic with exponential backoff",
    "chore: upgrade all dependencies to latest stable",
    "fix: eliminate race condition in concurrent scheduler",
    "feat: structured JSON logging with log levels",
    "refactor: extract config parsing into separate module",
    "fix: file writer now flushes buffer on exit",
    "feat: webhook event dispatch support",
    "perf: cache API responses to reduce rate-limit hits",
    "test: add integration tests for commit generator",
    "ci: add GitHub Actions workflow for linting",
    "fix: auth token refresh on 401 response",
    "feat: --verbose and --quiet flags",
]

PR_BODIES = [
    "Fixes the edge case discussed in the linked issue. All existing tests pass.",
    "Closes the feature request. Added new `commits_per_day` config option with validation.",
    "Dead code removed. No behaviour change expected.",
    "Easier to test and reason about — each function now has a single responsibility.",
    "Adds a null-check before processing the payload. Resolves the intermittent crash.",
    "Pass `--dry-run` to preview changes without writing. Useful for CI pipelines.",
    "Expanded the README with a quickstart, config reference, and FAQ section.",
    "Loop was using `<` instead of `<=`, causing the last day to be silently skipped.",
    "Uses exponential backoff with jitter, up to 4 retries before raising.",
    "All packages pinned to latest stable. Tested on Python 3.10, 3.11, 3.12.",
    "Added a threading lock around the shared scheduler queue. Fixes the race condition.",
    "Log records are now structured JSON — easy to ingest into ELK or Datadog.",
    "Config module is now independently testable. Covered by 8 new unit tests.",
    "Writer now explicitly calls `flush()` before closing the file handle.",
    "Dispatches a POST to the configured webhook URL after each batch of commits.",
]

# ================================================================
#  BUILD WEIGHTED COMMIT POOL ONCE
# ================================================================

_COMMIT_POPULATION  = list(COMMIT_WEIGHTS.keys())
_COMMIT_WEIGHT_LIST = list(COMMIT_WEIGHTS.values())

# ================================================================
#  UTILITIES
# ================================================================

def run(cmd, env=None, capture=False):
    return subprocess.run(
        cmd, check=True, env=env,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )

def git_time(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

def sorted_times_in_day(day: datetime, n: int):
    """Generate n sorted, gap-enforced random datetimes within `day`.
    70% of commits land in working hours (08:00-20:00)."""
    times = []
    for _ in range(n):
        if random.random() < 0.70:
            offset = random.randint(8 * 60, 20 * 60)
        else:
            offset = random.randint(0, 1439)
        times.append(day + timedelta(minutes=offset))
    times.sort()
    for i in range(1, len(times)):
        if times[i] <= times[i - 1]:
            times[i] = times[i - 1] + timedelta(minutes=1)
    return times

def generate_commit_message() -> str:
    action = random.choice(ACTIONS)
    scope  = random.choice(SCOPES)
    detail = random.choice(DETAILS)
    if random.random() < 0.45:
        return f"{action}({scope}): {detail}"
    return f"{action} {scope}: {detail}"

def choose_commits_today(in_burst: bool) -> int:
    base = random.choices(_COMMIT_POPULATION, weights=_COMMIT_WEIGHT_LIST, k=1)[0]
    if in_burst and base > 0:
        base += random.randint(BURST_BONUS_MIN, BURST_BONUS_MAX)
    return base

def progress_bar(day_num: int, total: int, label: str, width: int = 38):
    pct  = day_num / total if total else 1
    done = int(width * pct)
    bar  = "█" * done + "░" * (width - done)
    sys.stdout.write(f"\r  [{bar}] {day_num:>5}/{total}  {label}")
    sys.stdout.flush()

# ================================================================
#  CHECKPOINT
# ================================================================

def checkpoint_read():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            return datetime.strptime(open(CHECKPOINT_FILE).read().strip(), "%Y-%m-%d")
        except Exception:
            pass
    return None

def checkpoint_write(dt: datetime):
    with open(CHECKPOINT_FILE, "w") as f:
        f.write(dt.strftime("%Y-%m-%d"))

# ================================================================
#  API
# ================================================================

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept":        "application/vnd.github.v3+json",
}

# FIX 1: Normalize GITHUB_REPO — accepts full URL or plain repo name
_repo_name = GITHUB_REPO.rstrip("/").rstrip(".git").split("/")[-1]
API_BASE = f"https://api.github.com/repos/{GITHUB_USERNAME}/{_repo_name}"

# Shared rate-limit state — when we know we're exhausted, skip until reset time
_rate_limit_reset: float = 0.0   # epoch seconds when the limit resets

def _handle_rate_limit(headers) -> None:
    """Sleep until the GitHub rate-limit window resets using the response headers."""
    global _rate_limit_reset
    reset_ts = int(headers.get("X-RateLimit-Reset", 0))
    retry_after = int(headers.get("Retry-After", 0))
    if retry_after:
        wait = retry_after
    elif reset_ts:
        wait = max(reset_ts - int(time.time()), 1)
    else:
        wait = API_RETRY_DELAY
    _rate_limit_reset = time.time() + wait
    print(f"\n  Rate-limited — sleeping {wait}s until reset ...")
    time.sleep(wait)

def _is_rate_limited() -> bool:
    """Return True (and skip the call) if we know the window hasn't reset yet."""
    return time.time() < _rate_limit_reset

def api_request(method: str, path: str, payload=None):
    if _is_rate_limited():
        return None          # skip immediately, no wasted retries
    url = f"{API_BASE}/{path}"
    for attempt in range(1, API_MAX_RETRIES + 1):
        try:
            r = requests.request(method, url, headers=HEADERS, json=payload, timeout=20)
            if r.status_code in (429, 403):
                _handle_rate_limit(r.headers)
                if attempt < API_MAX_RETRIES:
                    continue
                return None
            if r.status_code not in (200, 201):
                print(f"\n  [!] {method} {path} -> HTTP {r.status_code}: {r.text[:120]}")
                return None
            return r.json()
        except requests.RequestException as exc:
            print(f"\n  [!] Network error (attempt {attempt}/{API_MAX_RETRIES}): {exc}")
            time.sleep(API_RETRY_DELAY * attempt)
    return None

def api_post(path, payload):  return api_request("POST",  path, payload)
def api_patch(path, payload): return api_request("PATCH", path, payload)

# Dedicated merge call — GitHub returns 204 No Content on success,
# not 200+JSON, so using api_post() would always see it as a failure.
def api_merge(pr_num: int, commit_title: str) -> bool:
    if _is_rate_limited():
        return False
    url = f"{API_BASE}/pulls/{pr_num}/merge"
    for attempt in range(1, API_MAX_RETRIES + 1):
        try:
            r = requests.put(url, headers=HEADERS, json={
                "commit_title": commit_title,
                "merge_method": "squash",
            }, timeout=20)
            if r.status_code in (200, 204):   # 204 = merged, no body
                return True
            if r.status_code in (405, 409):   # not mergeable / conflict
                print(f"\n  [!] Merge rejected ({r.status_code}): {r.text[:80]}")
                return False
            if r.status_code in (429, 403):
                _handle_rate_limit(r.headers)
                if attempt < API_MAX_RETRIES:
                    continue
                return False
            print(f"\n  [!] Merge -> HTTP {r.status_code}: {r.text[:80]}")
            return False
        except requests.RequestException as exc:
            print(f"\n  [!] Network error on merge (attempt {attempt}): {exc}")
            time.sleep(API_RETRY_DELAY * attempt)
    return False

def safe_push(branch: str):
    """Fetch remote, rebase local commits on top, then push.
    Handles the case where the remote has diverged (e.g. after a PR merge
    deletes/adds a commit), which causes a plain 'git push' to be rejected."""
    try:
        run(["git", "fetch", "origin", branch], capture=True)
        run(["git", "rebase", f"origin/{branch}"], capture=True)
    except subprocess.CalledProcessError:
        # Rebase failed (e.g. conflict) — abort and push with force-with-lease
        try:
            run(["git", "rebase", "--abort"], capture=True)
        except Exception:
            pass
        run(["git", "push", "--force-with-lease", "-u", "origin", branch])
        return
    run(["git", "push", "-u", "origin", branch])

# ================================================================
#  ISSUES
# ================================================================

def create_issue(title: str, body: str):
    data = api_post("issues", {"title": title, "body": body})
    if not data:
        return False
    num = data["number"]
    print(f"\n  Issue #{num}: {title}")
    if random.random() < 0.65:
        time.sleep(0.4)
        api_patch(f"issues/{num}", {"state": "closed"})
        print(f"     -> Closed")
    else:
        print(f"     -> Left open")
    return True

# ================================================================
#  PULL REQUESTS
# ================================================================

def create_pr(title: str, body: str, base_branch: str):
    temp    = f"auto/{random.randint(100_000, 999_999)}"
    pr_file = f".pr_{random.randint(1_000_000, 9_999_999)}.tmp"
    try:
        # FIX 3b: Sync local base with remote before branching.
        # fetch + reset handles diverged histories that --ff-only rejects.
        run(["git", "checkout", base_branch])
        run(["git", "fetch", "origin", base_branch], capture=True)
        run(["git", "reset", "--hard", f"origin/{base_branch}"], capture=True)

        run(["git", "checkout", "-b", temp])

        # FIX 3c: Use a unique temp file (not the shared LOG_FILE) so the branch
        # always has a real diff vs base — avoids "nothing to merge" 405 error
        with open(pr_file, "w") as f:
            f.write(f"pr | {temp} | {random.randint(1, 9_999_999)}\n")
        run(["git", "add", pr_file])
        run(["git", "commit", "-m", f"chore: branch work for '{title[:50]}'"])
        run(["git", "push", "origin", temp])
        run(["git", "checkout", base_branch])

        # Small delay so GitHub registers the branch before we open the PR
        time.sleep(1)

        pr = api_post("pulls", {
            "title": title, "body": body,
            "head": temp,  "base": base_branch,
        })
        if not pr:
            try:
                run(["git", "push", "origin", "--delete", temp], capture=True)
            except Exception:
                pass
            return False

        num = pr["number"]
        print(f"\n  PR #{num}: {title}")
        time.sleep(0.8)

        if random.random() < 0.72:
            ok = api_merge(num, f"Merge: {title}")
            if ok:
                print(f"     -> Merged")
            else:
                # Fall back to closing if merge failed
                api_patch(f"pulls/{num}", {"state": "closed"})
                print(f"     -> Merge failed, closed instead")
        else:
            api_patch(f"pulls/{num}", {"state": "closed"})
            print(f"     -> Closed without merge")

        # Clean up remote temp branch (may already be gone after squash merge)
        try:
            run(["git", "push", "origin", "--delete", temp], capture=True)
        except subprocess.CalledProcessError:
            pass

        if os.path.exists(pr_file):
            os.remove(pr_file)

        return True

    except subprocess.CalledProcessError as exc:
        print(f"\n  [!] PR branch error: {exc}")
        try:
            run(["git", "checkout", base_branch])
            run(["git", "branch", "-D", temp])
        except Exception:
            pass
        if os.path.exists(pr_file):
            os.remove(pr_file)
        return False

# ================================================================
#  STATS
# ================================================================

class Stats:
    def __init__(self):
        self.commits = self.issues = self.prs = 0
        self.active_days = self.max_day = 0

    def record_day(self, n: int):
        self.commits += n
        if n > 0:
            self.active_days += 1
            self.max_day = max(self.max_day, n)

    def report(self):
        print("\n")
        print("╔══════════════════════════════════════╗")
        print("║            Run Complete               ║")
        print("╠══════════════════════════════════════╣")
        print(f"║  Total commits   : {self.commits:<17} ║")
        print(f"║  Active days     : {self.active_days:<17} ║")
        print(f"║  Peak day        : {self.max_day:<17} ║")
        print(f"║  Issues created  : {self.issues:<17} ║")
        print(f"║  PRs created     : {self.prs:<17} ║")
        print("╚══════════════════════════════════════╝")
        print("\n  Check your GitHub contribution graph!\n")

# ================================================================
#  VALIDATION + SETUP
# ================================================================

def validate_config():
    errors = []
    if GITHUB_TOKEN == "YOUR_PAT_HERE":
        errors.append("GITHUB_TOKEN is not set")
    if not GITHUB_REPO or GITHUB_REPO == "YOUR_REPO_NAME_HERE":
        errors.append("GITHUB_REPO is not set")
    if errors:
        print("\n  Config errors - edit the CONFIG section at the top:\n")
        for e in errors:
            print(f"    * {e}")
        sys.exit(1)

def setup_git():
    run(["git", "config", "user.name",  GIT_NAME])
    run(["git", "config", "user.email", GIT_EMAIL])
    run(["git", "checkout", "-B", BRANCH])
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("# activity log - auto-generated\n")
        run(["git", "add", LOG_FILE])
        run(["git", "commit", "-m", "chore: init activity log"])

# ================================================================
#  MAIN
# ================================================================

def main():
    validate_config()
    setup_git()

    total_days  = (END_DATE - START_DATE).days + 1
    resume_from = checkpoint_read()

    if resume_from and resume_from > START_DATE:
        current = resume_from + timedelta(days=1)
        skipped = (current - START_DATE).days
        print(f"\n  Resuming from {current.strftime('%Y-%m-%d')} ({skipped} days already done)\n")
    else:
        current = START_DATE
        print(f"\n  Starting from {START_DATE.strftime('%Y-%m-%d')}\n")

    print(f"  Date range  : {START_DATE.strftime('%Y-%m-%d')} -> {END_DATE.strftime('%Y-%m-%d')}")
    print(f"  Total days  : {total_days}")
    print(f"  Commit dist : {min(COMMIT_WEIGHTS)}-{max(COMMIT_WEIGHTS)}/day  (weighted)")
    print(f"  Issues/week : ~{AVG_ISSUES_PER_WEEK}  |  PRs/week: ~{AVG_PRS_PER_WEEK}")
    print()

    random.shuffle(ISSUE_TITLES); issue_pool = ISSUE_TITLES * 15
    random.shuffle(PR_TITLES);    pr_pool    = PR_TITLES    * 15
    issue_idx = pr_idx = 0

    stats        = Stats()
    commit_buf   = 0
    burst_streak = 0

    while current <= END_DATE:
        date_str   = current.strftime("%Y-%m-%d")
        day_number = (current - START_DATE).days + 1

        # ── Burst logic ──────────────────────────────────────────
        if burst_streak > 0:
            in_burst     = True
            burst_streak -= 1
        elif random.random() < BURST_WEEK_PROBABILITY:
            in_burst     = True
            burst_streak = random.randint(3, 7)
        else:
            in_burst = False

        # ── How many commits today ────────────────────────────────
        n = choose_commits_today(in_burst)
        progress_bar(
            day_number, total_days,
            label=f"{date_str}  {'burst' if in_burst else '     '}  {n:>2} commits"
        )

        # ── Make commits ──────────────────────────────────────────
        if n > 0:
            times = sorted_times_in_day(current, n)
            # FIX: Write one unique log line per commit and stage+commit
            # individually so every commit has a real file diff.
            # GitHub ignores --allow-empty commits on the contribution graph —
            # that's why only 1 contribution was showing per day before.
            for ts in times:
                with open(LOG_FILE, "a") as f:
                    f.write(f"{date_str} | {random.randint(1, 9_999_999)}\n")
                run(["git", "add", LOG_FILE])
                env = os.environ.copy()
                env["GIT_AUTHOR_DATE"]    = git_time(ts)
                env["GIT_COMMITTER_DATE"] = git_time(ts)
                run(["git", "commit", "-m", generate_commit_message()], env=env)
                commit_buf += 1

            if commit_buf >= PUSH_BATCH_SIZE:
                safe_push(BRANCH)
                commit_buf = 0

        stats.record_day(n)

        # ── Issues & PRs — scheduled weekly, not rolled every day ────
        # Pick fixed days per week (Mon=0..Sun=6) to fire each action.
        # This keeps API call volume predictable and avoids hammering the
        # rate limit by firing on 57%/43% of days as before.
        dow = current.weekday()   # 0=Mon … 6=Sun
        week_num = (current - START_DATE).days // 7

        # Issue: fire on one chosen weekday per week (rotates each week)
        issue_day = week_num % 7
        if dow == issue_day and random.random() < (AVG_ISSUES_PER_WEEK / 7) * 7:
            ok = create_issue(
                issue_pool[issue_idx % len(issue_pool)],
                random.choice(ISSUE_BODIES),
            )
            if ok:
                stats.issues += 1
            issue_idx += 1

        # PR: fire on a different chosen weekday per week
        pr_day = (week_num + 3) % 7
        if dow == pr_day and random.random() < (AVG_PRS_PER_WEEK / 7) * 7:
            ok = create_pr(
                pr_pool[pr_idx % len(pr_pool)],
                random.choice(PR_BODIES),
                base_branch=BRANCH,
            )
            if ok:
                stats.prs += 1
            pr_idx += 1

        checkpoint_write(current)
        current += timedelta(days=1)

    # ── Final push ────────────────────────────────────────────────
    print("\n\n  Pushing final batch ...")
    safe_push(BRANCH)

    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)

    stats.report()


if __name__ == "__main__":
    main()