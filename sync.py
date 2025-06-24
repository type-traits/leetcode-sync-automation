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
- config/secrets.json (external, not version-controlled)
"""

import os
import json
import argparse
from leetcode_client import LeetCodeClient
from git_utils import GitHandler
from utils import format_filename, ensure_dir, save_solution, slugify
from rich import print

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

# 🧰 CLI argument parsing
parser = argparse.ArgumentParser(description="Sync LeetCode submissions to GitHub.")
parser.add_argument("--force-login", action="store_true", help="Force login and refresh cookies.")
parser.add_argument("--force-update", action="store_true", help="Force refresh of problem metadata")
args = parser.parse_args()

# Init clients
lc = LeetCodeClient(LC_USERNAME, LC_PASSWORD, force_update=args.force_update)
git = GitHandler(SOLUTIONS_REPO_PATH)

if args.force_login:
    print("[cyan]📡 Force login activated — launching fresh login...[/cyan]")
else:
    print("[cyan]📡 Logging into LeetCode using stored session (if valid)...[/cyan]")
    
lc.login(force=args.force_login)

print("[green]✅ Fetching submissions...[/green]")
submissions = lc.get_accepted_submissions()

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
        print(f"[yellow]🔁 Skipping {title} [{lang}] — already committed[/yellow]")
        continue

    print(f"[blue]📄 Saving: {rel_path}[/blue]")
    ensure_dir(os.path.dirname(abs_path))
    save_solution(abs_path, code)

    # Commit the file
    commit_msg = f"Add solution for {pid}. {title} [{lang}]"
    git.commit_file(rel_path, commit_msg)

    # Update state
    committed.setdefault(pid, []).append(lang)

# Save updated commit state
with open(COMMITTED_PATH, "w") as f:
    json.dump(committed, f, indent=2)

print("[bold green]🎉 Done syncing LeetCode submissions![/bold green]")
