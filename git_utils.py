# git_utils.py

"""
Git Utilities Module: Handles file staging, committing, and pushing to GitHub.

Functionality:
---------------
- Initializes a GitPython Repo object for the `leetcode-solutions` directory.
- Adds a file to the staging index.
- Creates a single commit per file with a descriptive message.
- Pushes changes to the remote repo automatically.

This ensures that each LeetCode submission is committed separately, maintaining
a clean and readable commit history.

Dependencies:
-------------
- GitPython (install with `pip3 install GitPython`)
"""

import os
from git import Repo
from rich import print


class GitHandler:
    def __init__(self, repo_path):
        if not os.path.exists(repo_path):
            raise ValueError(f"Repo path not found: {repo_path}")
        self.repo_path = repo_path
        self.repo = Repo(repo_path)
        if self.repo.bare:
            raise ValueError("The specified repo path is a bare repository.")

    def commit_file(self, rel_file_path, commit_msg):
        """
        Stages, commits, and pushes a file to the remote repo.
        """
        abs_file_path = os.path.join(self.repo_path, rel_file_path)

        if not os.path.exists(abs_file_path):
            raise FileNotFoundError(f"File not found: {abs_file_path}")

        self.repo.git.add(rel_file_path)

        if self.repo.is_dirty(index=True, working_tree=False, untracked_files=False):
            self.repo.index.commit(commit_msg)
            origin = self.repo.remote(name='origin')
            origin.push()
            print(f"[green]✅ Committed and Pushed.[/green] {rel_file_path}")
        else:
            print(f"[gray]🟢 No changes to commit for: {rel_file_path}[/gray]")
