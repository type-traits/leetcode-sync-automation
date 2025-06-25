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
import sys
import time
import json
from urllib.parse import urljoin
from slugify import slugify

COOKIES_FILE = "config/cookies.json"
PROBLEM_METADATA_PATH = "state/problem_metadata.json"

class LeetCodeClient:
    BASE_URL = "https://leetcode.com"
    GRAPHQL_URL = "https://leetcode.com/graphql"
    CONTENT_TYPE_JSON = {"Content-Type": "application/json"}
    SUBMISSIONS_URL = "https://leetcode.com/api/submissions/"
    PROBLEMS_URL = "https://leetcode.com/problems/api/problems/algorithms/"

    def __init__(self, username, password, force_update=False):
        from logger import get_logger, get_log_and_print
        self.log = get_logger()
        self.log_and_print = get_log_and_print()
        self.username = username
        self.password = password
        self.force_update = force_update
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False, slow_mo=50)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.cookies = None
    
    def debug_save_html(self, page, filename="page_snapshot.html"):
        """
        Saves the full HTML content of the current page to a file
        and optionally pauses execution.
        """
        html = page.content()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        self.log_and_print.info(f"Saved HTML to {filename}.", style="cyan", emoji="📄")
        # Uncomment below if you want to pause
        # input("🛑 Script paused. Press Enter to continue.")

    
    def is_user_premium(self) -> bool:
        """
        Checks whether the currently logged-in user is a LeetCode Premium member.
        Returns True if premium, False otherwise.
        """
        query = """
        query globalData {
        userStatus {
            isSignedIn
            isPremium
        }
        }
        """
        response = self.page.request.post(
            url=self.GRAPHQL_URL,
            headers=self.CONTENT_TYPE_JSON,
            data=json.dumps({
                "query": query,
                "variables": {},
                "operationName": "globalData"
            })
        )

        result = response.json()
        status = result.get("data", {}).get("userStatus", {})
        return status.get("isPremium", False)


    def get_company_tags_for_slug(self, title_slug: str) -> list:
        """
        Fetches company tags for a single problem using its titleSlug.
        Returns a list of company names.
        """
        self.log.info("Fetching company tags for: {slug}")

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
            url=self.GRAPHQL_URL,
            headers=self.CONTENT_TYPE_JSON,
            data=json.dumps({
                "query": query,
                "variables": variables,
                "operationName": "questionTitle"
            })
        )

        result = response.json()

        if "errors" in result:
            self.log_and_print.warning("Could not fetch company tags for {title_slug}", style="yellow", emoji="⚠️")
            return []

        tags = result["data"]["question"]["companyTags"]
        return [tag["name"] for tag in tags]
    
    def save_company_tags_json(self, problems, output_path="state/company_tags.json"):
        """
        Fetches company tags for a list of problems and saves to a JSON file.
        `problems` should be a list of dicts with keys: titleSlug and questionFrontendId
        """
        self.log.info("Fetching company tags for all problems...")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        result = {}

        for problem in problems:
            slug = problem["titleSlug"]
            qid = problem["questionFrontendId"]

            try:
                tags = self.get_company_tags_for_slug(slug)
                result[slug] = tags
            except Exception as e:
                self.log.exception(f"Failed to fetch company tags for {slug}: {e}")
                self.log_and_print.warning(
                    f"⚠️ Company tag fetch failed for {slug}. Aborting early.",
                    style="yellow"
                )
                break

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        self.log_and_print.success("Saved company tags to {output_path}", style="green", emoji="✅")


    def get_all_problem_metadata(self, force_refresh=False) -> list:
        """
        Returns a list of all LeetCode problem metadata, either from cache or by calling GraphQL.
        Also triggers company tag fetch if user is Premium.
        """
        if not force_refresh and os.path.exists(PROBLEM_METADATA_PATH):
            self.log.debug("Using cached problem metadata.")
            with open(PROBLEM_METADATA_PATH, "r") as f:
                questions = json.load(f)
        else :           
            self.log.info("Fetching problem metadata from LeetCode...")
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
                url=self.GRAPHQL_URL,
                headers=self.CONTENT_TYPE_JSON,
                data=json.dumps({
                    "query": query,
                    "variables": variables,
                    "operationName": "problemsetQuestionListV2"
                })
            )
            json_result = response.json()

            try:
                if "data" not in json_result or "problemsetQuestionListV2" not in json_result["data"]:
                    raise ValueError(f"GraphQL response failed: {json_result.get('errors', 'unknown error')}")
            except Exception as e:
                self.log_and_print.exception("❌ Failed to fetch problem metadata from GraphQL", exc=e)
                sys.exit(1)  # Gracefully terminate the script

            questions = json_result["data"]["problemsetQuestionListV2"]["questions"]

            os.makedirs(os.path.dirname(PROBLEM_METADATA_PATH), exist_ok=True)
            with open(PROBLEM_METADATA_PATH, "w", encoding="utf-8") as f:
                json.dump(questions, f, indent=2)
            
            self.log_and_print.success("Saved problem metadata to {PROBLEM_METADATA_PATH}", style="green", emoji="✅")

            # Feature: fetch company Tags and store to state/company_tags.json
            if self.is_user_premium():
                self.log_and_print.success("🥇 Premium account detected.", style="green", emoji="🥇")
                self.save_company_tags_json(questions)
            else:
                self.log_and_print.warning("Not a Premium account. Company tags won't be available.", style="red", emoji="⚠️")

        return questions
    
    def save_cookies(self):
        cookies = self.context.cookies()
        os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f, indent=2)

    def validate_cookies(self) -> bool:
        self.page.goto(f"{self.BASE_URL}/submissions/")
        try:
            self.page.wait_for_selector("#navbar_user_avatar", timeout=5000)
            return True
        except:
            self.log_and_print.warning("Cookies invalid. Re-authentication required.", style="yellow", emoji="⚠️")
            return False

    def login(self, force=False):
        if force:
            self.log_and_print.warning("Force login requested. Skipping stored cookies...", style="red", emoji="⚠️")
        elif os.path.exists(COOKIES_FILE):
            self.log_and_print.info("Using stored cookies...", style="cyan", emoji="🔁")
            with open(COOKIES_FILE, "r") as f:
                cookies = json.load(f)
            self.context.add_cookies(cookies)
            self.page = self.context.new_page()

            # ✅ Validate cookies
            if self.validate_cookies():
                self.log_and_print.success("Cookies valid. Logged in.", style="green", emoji="✅")
                return                
        else:
            self.log_and_print.error("No cookies found. Launching browser for manual login...", style="red", emoji="🛑")

        # 🔁 Manual login
        self.page = self.context.new_page()
        self.page.goto(f"{self.BASE_URL}/accounts/login/")
        if not force:
            self.log.info("Auto-filling login fields from config...")
            self.page.fill('input[name="login"]', self.username)
            self.page.fill('input[name="password"]', self.password)
            self.page.focus('input[name="password"]')
        else:
            self.log.info("Force login active — clearing login fields...")
            self.page.fill('input[name="login"]', "")
            self.page.fill('input[name="password"]', "")

        self.log_and_print.info("Please solve the CAPTCHA and log in manually.", style="magenta", emoji="👉")
        self.page.wait_for_selector("#navbar_user_avatar", timeout=300000)

        # 💾 Save cookies
        self.save_cookies()
        self.log_and_print.success("Login successful. Cookies saved!", style="green", emoji="✅")

    def get_accepted_submissions(self):
        submissions = []
        offset = 0
        limit = 20

        self.page.goto("https://leetcode.com/problemset/")
        self.page.wait_for_selector("script#__NEXT_DATA__", state="attached")

        # debug_save_html(self.page)

        questions = self.get_all_problem_metadata(self.force_update)

        id_map = {
            q["titleSlug"]: q["questionFrontendId"]
            for q in questions
        }

        self.log.info("Fetching accepted submissions from API...")
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
