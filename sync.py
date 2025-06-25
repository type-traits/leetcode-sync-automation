"""
Main Sync Script: Coordinates the full LeetCode → GitHub automation flow.

Functionality:
---------------
- Loads user credentials and solution repo path from `config/secrets.json`.
- Initializes LeetCode client to log in and fetch accepted submissions.
- Formats filenames and organizes solutions by language (e.g., cpp/, python/).
- Skips already-committed problems using `state/committed.json`.
- Writes new solutions to the correct folder in the solutions repo.
- Commits and pushes each new solution as a separate Git commit.

Key Features:
-------------
- Ensures one commit per problem per language (1:1 relationship).
- Tracks state to avoid duplicate commits.
- Supports multiple languages for the same problem.
- Designed for regular use (daily/weekly local run).

Dependencies:
-------------
- leetcode_client.py
- git_utils.py
- utils.py
- logger.py
- config/secrets.json (external, not version-controlled)
"""

import os
import json
import argparse
from leetcode_client import LeetCodeClient
from git_utils import GitHandler
from utils import format_filename, ensure_dir, save_solution, slugify
from logger import init_logger, get_logger, get_log_and_print

def format_skipped_pretty(skipped_list, spacing=44):
    """
    Pretty-prints skipped submissions in aligned 2-column layout,
    where shorter titles appear on the left and longer ones on the right.

    Format:
        - {shorter_title} [lang]    - {longer_title} [lang]

    This improves log readability by balancing short and long titles
    in visually aligned columns.

    Args:
        skipped_list (list of dict): Each item must have 'title' and 'lang' keys.
        spacing (int): Minimum column width for left entries to align the right column.

    Example Output:
        - Two Sum [cpp]                - Bitwise AND of Numbers Range [cpp]
        - Plus One [cpp]              - Reveal Cards In Increasing Order [cpp]
    """
    sorted_skipped = sorted(skipped_list, key=lambda x: len(x['title']))
    
    lines = []
    n = len(sorted_skipped)
    mid = n // 2
    for i in range(mid):
        left = sorted_skipped[i]
        right = sorted_skipped[-(i + 1)]
        left_str = f"- {left['title']} [{left['lang']}]".ljust(spacing)
        right_str = f"- {right['title']} [{right['lang']}]"
        lines.append(left_str + right_str)

    # Handle odd count
    if n % 2 == 1:
        center = sorted_skipped[mid]
        lines.append(f"- {center['title']} [{center['lang']}]")

    return "\n".join(lines)

# 🧰 CLI argument parsing
parser = argparse.ArgumentParser(description="Sync LeetCode submissions to GitHub.")
parser.add_argument("--force-login", action="store_true", help="Force login and refresh cookies.")
parser.add_argument("--force-update", action="store_true", help="Force refresh of problem metadata")
parser.add_argument(
    "--log-level",
    default="INFO",
    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    help="Set the logging level (default: INFO)"
)

args = parser.parse_args()

# Init logger
init_logger(level_str=args.log_level)
log = get_logger()
log_and_print = get_log_and_print()

from leetcode_client import LeetCodeClient # leetcode_client has top-level dependency of logger.

# Load secrets
with open("config/secrets.json", "r") as f:
    secrets = json.load(f)

LC_USERNAME = secrets["leetcode_username"]
LC_PASSWORD = secrets["leetcode_password"]
SOLUTIONS_REPO_PATH = secrets["solutions_repo_path"]
COMMITTED_PATH = "state/committed.json"

# Ensure committed.json exists
if not os.path.exists(COMMITTED_PATH):
    with open(COMMITTED_PATH, "w") as f:
        json.dump({}, f)

with open(COMMITTED_PATH, "r") as f:
    committed = json.load(f)

# Init clients
lc = LeetCodeClient(LC_USERNAME, LC_PASSWORD, force_update=args.force_update)
git = GitHandler(SOLUTIONS_REPO_PATH)

if args.force_login:
    log_and_print.info("Force login activated — launching fresh login...", style="cyan", emoji="📡")
else:
    log_and_print.info("Logging into LeetCode using stored session (if valid)...", style="cyan", emoji="📡")
    
lc.login(force=args.force_login)

log_and_print.info("Fetching submissions...", style="magenta", emoji="📥")
submissions = lc.get_accepted_submissions()
skipped = []

for sub in submissions:
    pid = sub["question_id"]
    title = sub["title"]
    lang = sub["lang"]
    code = sub["code"]

    lang_folder = lang.lower()
    filename = format_filename(pid, title, lang)
    rel_path = os.path.join(lang_folder, filename)
    abs_path = os.path.join(SOLUTIONS_REPO_PATH, rel_path)

    # Already committed?
    if pid in committed and lang in committed[pid]:
        log.debug(f"Skipping {title} [{lang}] — already committed")
        skipped.append({"title": title, "lang": lang})
        continue

    log_and_print.info(f"Saving: {rel_path}", style="blue", emoji="📄")
    ensure_dir(os.path.dirname(abs_path))
    save_solution(abs_path, code)

    # Commit the file
    commit_msg = f"Add solution for {pid}. {title} [{lang}]"
    git.commit_file(rel_path, commit_msg)

    # Update state
    committed.setdefault(pid, []).append(lang)

if skipped:
    log_and_print.info(f"{len(skipped)} submissions skipped (already committed).", style="magenta", emoji="🔁")
    log.info(f"Skipped problems ({len(skipped)}):\n{format_skipped_pretty(skipped)}")

# Save updated commit state
with open(COMMITTED_PATH, "w") as f:
    json.dump(committed, f, indent=2)

log_and_print.success("Done syncing LeetCode submissions!", style="bold green", emoji="🎉")
