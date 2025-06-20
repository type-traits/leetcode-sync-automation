# LeetCode Sync Automation

📌 Automatically fetch accepted LeetCode submissions and push them to a separate GitHub repo — with one commit per problem per language.

---

## 📂 Folder & File Layout

leetcode-sync-automation/
├── config/
│   └── (ignored by .gitignore)
├── state/
│   └── committed.json        # Tracks submitted problems (auto-created)
├── leetcode_client.py        # LeetCode login & fetch code
├── git_utils.py              # Git add, commit, push
├── utils.py                  # Slugify, filename builder, etc.
├── sync.py                   # 🔁 Main runner script
├── .gitignore
├── LICENSE                   # MIT
└── README.md
--------------------------------

## 🔐 Config: `config/secrets.json`

This file stores your LeetCode login credentials and the path to your solutions repo.

> ⚠️ This file should always be kept outside version control (already in `.gitignore`)

### ✅ Example

```json
{
  "leetcode_username": "your_leetcode_username",
  "leetcode_password": "your_leetcode_password",
  "solutions_repo_path": "../leetcode-solutions"
}

🔧 Setup Instructions
1. Clone both repos

git clone https://github.com/yourname/leetcode-sync-automation
git clone https://github.com/yourname/leetcode-solutions

2. Install required dependencies

pip3 install playwright GitPython python-slugify rich
python3 -m playwright install

3. Add your secrets.json
Place your login credentials in a safe location, like this:

    leetcode/config/secrets.json

🚀 Run the Script
From the leetcode-sync-automation/ folder:

python3 sync.py

It will:

Log into LeetCode

Fetch accepted solutions

Save them in leetcode-solutions/ under folders like cpp/, python/

Commit & push them, one commit per problem per language