"""
LeetCodeClient: Handles authentication and data extraction from LeetCode.

Functionality:
---------------
- Logs into LeetCode using Playwright (headless browser automation).
- Fetches a mapping of all algorithm problems and their question IDs.
- Retrieves accepted submission history via LeetCode's internal API.
- Extracts clean metadata per problem (ID, title, language, code).
- Maps language names to normalized folder names.
- Returns submissions as a list of dictionaries for further processing.

Dependencies:
-------------
- playwright
- slugify
- python-rich

This client is designed to be called from sync.py and is reusable for
additional features like filtering by date, topic, etc.
"""

from playwright.sync_api import sync_playwright
import os
import time
import json
from urllib.parse import urljoin
from slugify import slugify
from rich import print

COOKIES_FILE = "config/cookies.json"

def debug_save_html(page, filename="page_snapshot.html"):
    """
    Saves the full HTML content of the current page to a file
    and optionally pauses execution.
    """
    html = page.content()
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"📄 Saved HTML to {filename}.")
    # Uncomment below if you want to pause
    # input("🛑 Script paused. Press Enter to continue.")

class LeetCodeClient:
    BASE_URL = "https://leetcode.com"
    SUBMISSIONS_URL = "https://leetcode.com/api/submissions/"
    PROBLEMS_URL = "https://leetcode.com/problems/api/problems/algorithms/"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False, slow_mo=50)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.cookies = None

    def get_company_tags_for_slug(self, title_slug: str) -> list:
        """
        Fetches company tags for a single problem using its titleSlug.
        Returns a list of company names.
        """
        print(f"[cyan]🔍 Fetching company tags for: {title_slug}[/cyan]")

        query = """
        query questionTitle($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            companyTags {
            name
            slug
            }
        }
        }
        """

        variables = {"titleSlug": title_slug}
        response = self.page.request.post(
            url="https://leetcode.com/graphql",
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                "query": query,
                "variables": variables,
                "operationName": "questionTitle"
            })
        )

        result = response.json()

        if "errors" in result:
            print(f"[yellow]⚠️ Could not fetch company tags for {title_slug}[/yellow]")
            return []

        tags = result["data"]["question"]["companyTags"]
        return [tag["name"] for tag in tags]
    
    def save_company_tags_json(self, problems, output_path="state/company_tags.json"):
        """
        Fetches company tags for a list of problems and saves to a JSON file.
        `problems` should be a list of dicts with keys: titleSlug and questionFrontendId
        """
        print("[cyan]🏷️  Fetching company tags for all problems...[/cyan]")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        result = {}

        for problem in problems:
            slug = problem["titleSlug"]
            qid = problem["questionFrontendId"]

            try:
                tags = self.get_company_tags_for_slug(slug)
                result[slug] = tags
            except Exception as e:
                print(f"[red]❌ Failed to fetch company tags for {slug}[/red]")
                print("[yellow]⚠️ Aborting company tag collection early.[/yellow]")
                break  # 🔁 Exit loop immediately if any error occurs

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        print(f"[green]✅ Saved company tags to {output_path}[/green]")


    def get_problem_id_map_from_graphql(self):
        query = """
        query problemsetQuestionListV2($filters: QuestionFilterInput, $limit: Int, $searchKeyword: String, $skip: Int, $sortBy: QuestionSortByInput, $categorySlug: String) {
        problemsetQuestionListV2(
            filters: $filters
            limit: $limit
            searchKeyword: $searchKeyword
            skip: $skip
            sortBy: $sortBy
            categorySlug: $categorySlug
        ) {
            questions {
            questionFrontendId
            titleSlug
            difficulty
            }
            totalLength
            hasMore
        }
        }
        """

        variables = {
            "skip": 0,
            "limit": 4000,
            "categorySlug": "all-code-essentials",
            "searchKeyword": "",
            "filters": {
                "filterCombineType": "ALL",
                "statusFilter": {"questionStatuses": [], "operator": "IS"},
                "difficultyFilter": {"difficulties": [], "operator": "IS"},
                "languageFilter": {"languageSlugs": [], "operator": "IS"},
                "topicFilter": {"topicSlugs": [], "operator": "IS"},
                "acceptanceFilter": {},
                "frequencyFilter": {},
                "frontendIdFilter": {},
                "lastSubmittedFilter": {},
                "publishedFilter": {},
                "companyFilter": {"companySlugs": [], "operator": "IS"},
                "positionFilter": {"positionSlugs": [], "operator": "IS"},
                "premiumFilter": {"premiumStatus": [], "operator": "IS"}
            },
            "sortBy": {
                "sortField": "CUSTOM",
                "sortOrder": "ASCENDING"
            }
        }

        response = self.page.request.post(
            url="https://leetcode.com/graphql",
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                "query": query,
                "variables": variables,
                "operationName": "problemsetQuestionListV2"
            })
        )

        result = response.json()
        if "data" not in result or "problemsetQuestionListV2" not in result["data"]:
            raise ValueError(f"❌ GraphQL response failed: {result.get('errors', 'unknown error')}")

        questions = result["data"]["problemsetQuestionListV2"]["questions"]
        id_map = {
            q["titleSlug"]: q["questionFrontendId"]
            for q in questions
        }

        output_path = "state/problem_metadata.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2)
        
        print(f"[green]✅ Saved problem metadata to {output_path}[/green]")

        # Feature: fetch company Tags and store to state/company_tags.json
        # self.save_company_tags_json(questions)

        return id_map
    
    
    def login(self, force=False):
        if force:
            print("[red]⚠️ Force login requested. Skipping stored cookies...[/red]")
        elif os.path.exists(COOKIES_FILE):
            print("[cyan]🔁 Using stored cookies...[/cyan]")
            with open(COOKIES_FILE, "r") as f:
                cookies = json.load(f)
            self.context.add_cookies(cookies)
            self.page = self.context.new_page()

            # ✅ Validate cookies
            self.page.goto(f"{self.BASE_URL}/submissions/")
            try:
                self.page.wait_for_selector("#navbar_user_avatar", timeout=5000)
                print("[green]✅ Cookies valid. Logged in.[/green]")
                return
            except:
                print("[yellow]⚠️ Cookies invalid. Re-authentication required.[/yellow]")
        else:
            print("[red]🛑 No cookies found. Launching browser for manual login...[/red]")

        # 🔁 Manual login
        self.page = self.context.new_page()
        self.page.goto(f"{self.BASE_URL}/accounts/login/")
        print("👉 Please log in manually and solve the CAPTCHA.")
        self.page.wait_for_selector("#navbar_user_avatar", timeout=300000)

        # 💾 Save cookies
        cookies = self.context.cookies()
        os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f, indent=2)
        print("[green]✅ Login successful. Cookies saved![/green]")


    def get_accepted_submissions(self):
        submissions = []
        offset = 0
        limit = 20

        print("[magenta]📥 Fetching problem metadata...[/magenta]")
        self.page.goto("https://leetcode.com/problemset/")
        self.page.wait_for_selector("script#__NEXT_DATA__", state="attached")

        # debug_save_html(self.page)

        id_map = self.get_problem_id_map_from_graphql()

        print("[magenta]🔄 Fetching accepted submissions from API...[/magenta]")
        while True:
            url = f"{self.SUBMISSIONS_URL}?offset={offset}&limit={limit}"
            self.page.goto(url)
            body = self.page.evaluate("() => JSON.parse(document.body.innerText)")
            submission_list = body.get("submissions_dump", [])

            if not submission_list:
                break

            for sub in submission_list:
                if sub["status_display"] != "Accepted":
                    continue
                if not sub.get("code") or not sub.get("title_slug"):
                    continue

                slug = sub["title_slug"]
                submissions.append({
                    "question_id": id_map.get(slug, "0"),
                    "title": sub["title"],
                    "lang": self.map_lang(sub["lang"]),
                    "code": sub["code"]
                })

            offset += limit
            time.sleep(0.5)

        return submissions

    def map_lang(self, lang):
        """
        Maps LeetCode language display names to folder-friendly names
        """
        mapping = {
            "cpp": "cpp",
            "python3": "python",
            "java": "java",
            "c": "c",
            "golang": "go",
            "rust": "rust"
        }
        return mapping.get(lang.lower(), slugify(lang.lower()))

    def close(self):
        self.browser.close()
        self.playwright.stop()
