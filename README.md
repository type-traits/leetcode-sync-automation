# LeetCode Sync Automation

> 🧠 Automatically fetch accepted LeetCode submissions and sync them to a structured GitHub repo, with one commit per problem per language.

---

## 📁 Project Structure

```
leetcode-sync-automation/
├── sync.py                  # Main script runner
├── leetcode_client.py       # Handles login & fetching submissions
├── git_utils.py             # Commits and stages files
├── utils.py                 # Filename helpers and utilities
├── config/
│   ├── secrets.json         # LeetCode credentials (ignored)
│   └── cookies.json         # Session cookie after login
├── state/
│   ├── committed.json       # Tracks committed problems
│   └── problem_metadata.json# Cached metadata from GraphQL
├── .gitignore               # Ignores local/session/state files
├── LICENSE                  # Apache 2.0 License
└── README.md                # This file
```

---

## 🚀 Features

- ✅ Logs into your LeetCode account (with cookies or credentials)
- ✅ Fetches all **accepted submissions**
- ✅ Saves them in language-specific folders: `cpp/`, `python/`, `java/` etc.
- ✅ Each problem committed exactly once per language
- ✅ Uses LeetCode problem ID in filenames: `1_two_sum.cpp`
- ✅ Commits each file as a separate Git commit
- ✅ Optionally saves full problem metadata for later use

---

## ⚙️ Initial Setup


### 1. Create a separate repo for your solutions

```bash
mkdir leetcode-solutions-repo
cd leetcode-solutions-repo
git init
touch README.md              # or add your existing files
git add .
git commit -m "Initial commit"
git remote add origin git@github.com:your-username/my-project.git
git branch -M main
git push -u origin main
```

### 2. Clone this repo

```bash
git clone git@github.com:type-traits/leetcode-sync-automation.git
cd leetcode-sync-automation
```

### 3. Create `config/secrets.json` with following content

```json
{
  "leetcode_username": "your_leetcode_username",
  "leetcode_password": "your_leetcode_password",
  "solutions_repo_path": "../leetcode-solutions"
}
```

Or leave credentials out and log in manually (cookies will be saved).

---

## 🧠 Running the Script

```bash
python3 sync.py
```

- Browser will open on first run (non-headless)
- You manually log in and solve CAPTCHA
- Cookies will be stored in `config/cookies.json`
- From then on, sync is automated

---

## 💾 Output Format

Each submission is saved like:

```
cpp/1_two_sum.cpp
python/121_best_time_to_buy_and_sell_stock.py
```

**Commit Message Example:**
```
Add solution for 121. Best Time to Buy and Sell Stock [Python]
```

## 🔐 Cookie Management & Session Expiry

This script uses your LeetCode session cookies to avoid logging in every time.

- On first run, you'll manually log in using a browser (CAPTCHA may appear)
- Your session cookie will be saved to `config/cookies.json`
- On future runs, the script uses this cookie to stay logged in automatically

### 🕒 Do cookies expire?

Yes. LeetCode sessions typically expire after 2–4 weeks or if you manually log out from the site.

The script checks for validity by visiting a protected page. If the session is invalid:

- You'll be prompted to log in again
- A new cookie will be saved

### 💡 To manually force re-login:

You can delete the saved cookie file:

```bash
rm config/cookies.json
```

---

## 🔐 .gitignore Highlights

```
.DS_Store
__pycache__/
config/
state/
.env
```

---

## 📜 License

This project is licensed under the [Apache 2.0 License](./LICENSE).

---

## 🙋 FAQ

- **Q:** What if I switch programming languages?  
  **A:** Submissions go into separate folders per language (`cpp/`, `python/`, etc.), and a new commit is created.

- **Q:** What if I want to re-sync everything?  
  **A:** Delete `state/committed.json` and rerun.

- **Q:** Can I run this on GitHub Actions?  
  **A:** Not directly, because login requires CAPTCHA. But once cookies are stored, it can run locally without user input.

---

## ✨ Future Ideas

- `--dry-run` mode
- Generate README index of solved problems
- Markdown export per problem
- Filter by difficulty or tags

---

Automated with ❤️ by [Chandra Prakash Dixit](https://in.linkedin.com/in/dixit-chandra)
