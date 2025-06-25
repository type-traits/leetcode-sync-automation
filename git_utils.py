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

class GitHandler:
    def __init__(self, repo_path):
        from logger import get_logger, get_log_and_print  # ✅ safe now
        self.log = get_logger()
        self.log_and_print = get_log_and_print()
        try:
            if not os.path.exists(repo_path):
                raise ValueError(f"Repo path not found: {repo_path}")
        except Exception as e:
            self.log_and_print.exception("Invalid repository path.", e)
            raise

        self.repo_path = repo_path
        self.repo = Repo(repo_path)
        try:
            if self.repo.bare:
                raise ValueError("The specified repo path is a bare repository.")
        except Exception as e:
            self.log_and_print.exception("Git repository is bare — cannot proceed.", e)
            raise


    def commit_file(self, rel_file_path, commit_msg):
        """
        Stages, commits, and pushes a file to the remote repo.
        """
        abs_file_path = os.path.join(self.repo_path, rel_file_path)

        try:
            if not os.path.exists(abs_file_path):
                raise FileNotFoundError(f"File not found: {abs_file_path}")
        except Exception as e:
            self.log_and_print.exception(f"Cannot commit — file missing: {abs_file_path}", e)
            raise


        self.repo.git.add(rel_file_path)

        if self.repo.is_dirty(index=True, working_tree=False, untracked_files=False):
            self.repo.index.commit(commit_msg)
            origin = self.repo.remote(name='origin')
            origin.push()
            self.log_and_print.success(f"Committed and Pushed. {rel_file_path}", style="green", emoji="✅")
        else:
            self.log.debug("No changes to commit for: {rel_file_path}")
