# 🧠 LeetCode Sync Automation

Automatically sync your accepted LeetCode submissions to a structured GitHub repository.

---

## 🚀 Features

- 🔐 **Login via browser** (Playwright) — includes CAPTCHA support
- 🍪 **Stored cookie session** to avoid re-login
- 📄 **Fetches all accepted submissions** using LeetCode's private API
- 📁 **Auto-formats filenames** and organizes them by language (`cpp/`, `python/`, etc.)
- ✅ **One commit per solution** — prevents duplication
- 🧠 **Maintains committed state** using `state/committed.json`
- 🏷️ **Premium support**: Fetch company tags for each problem (Premium-only)
- 📡 **GraphQL-powered metadata** with optional cache refresh
- 🔁 **Command-line control** for login/session refresh and log level
- 📜 **Structured logging system** (color-coded CLI + persistent log files)

---

## 🧩 CLI Arguments

This script supports flexible command-line arguments to control its behavior:

### `--force-login`

Skips stored session cookies (if any) and launches a fresh browser-based login flow.

```bash
python3 sync.py --force-login
```

Use this when:
- Your session has expired or is invalid
- You want to log in with a different LeetCode account
- You're debugging login-related issues

### `--force-update`

Forces a refresh of problem metadata from LeetCode’s GraphQL API, overriding the local cache.

```bash
python3 sync.py --force-update
```

Use this when:
- New problems have been added or modified on LeetCode
- You want updated tags, difficulty, or titles

### `--log-level`

Controls verbosity of logs shown on the console and written to file.

```bash
python3 sync.py --log-level DEBUG
```

Available levels:
- `DEBUG`: Everything (verbose)
- `INFO`: Normal operation messages
- `WARNING`: Skippable issues
- `ERROR`: Serious problems only

Defaults to `INFO`.

---

## 🛠️ Setup & Prerequisites

### 🔹 Python Version

Python **3.9 or higher** is recommended.

### 📦 Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Also install Playwright’s browser binaries:

```bash
playwright install
```

### 🔐 Secrets

You’ll need a `config/secrets.json` file:

```json
{
  "leetcode_username": "your_username",
  "leetcode_password": "your_password",
  "solutions_repo_path": "/absolute/path/to/your/solutions-repo"
}
```

### 📁 Repo Structure

```
leetcode-sync-automation/
├── sync.py
├── leetcode_client.py
├── git_utils.py
├── logger.py
├── utils.py
├── config/
│   └── secrets.json
├── state/
│   ├── committed.json
│   ├── company_tags.json
│   └── problem_metadata.json
└── logs/
    └── sync_YYYY-MM-DDTHH-MM-SS.log
```

---

## 📊 Logging System

This project uses a unified, styled logging system (`logger.py`):

- 🖨️ **Styled CLI output** via `rich`
- 🧾 **Persistent logs** to `logs/sync_<timestamp>.log`
- 🛠️ Powered by a singleton-style `SyncLogger`

You can log using:

```python
from logger import log, log_and_print

log.info("Developer-only log")
log_and_print.success("User-facing log with style and emoji")
```

Logs like `log.debug(...)` go to **file only**, while `log_and_print.info(...)` goes to **both file and CLI**.

---

## ✅ Commit Structure

- One commit per accepted submission per language
- Format: `Add solution for 1. Two Sum [cpp]`
- Already committed solutions are skipped

---

## 🔒 Premium Support

If your LeetCode account is Premium, company tags will be fetched and saved to `state/company_tags.json`.

---

## 🤝 Contributing

Pull requests, feature ideas, and improvements are welcome!

---

Automated with ❤️ by [Chandra Prakash Dixit](https://in.linkedin.com/in/dixit-chandra)
