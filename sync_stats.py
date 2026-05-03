import os
import re
import sys
import json
import logging
import datetime
from datetime import timezone, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# --- Configuration ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_REPOSITORY_OWNER")
README_PATH = "README.md"
GRAPHQL_ENDPOINT = "https://api.github.com/graphql"

def get_session():
    """Configure requests session with exponential backoff for resiliency."""
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def fetch_graphql_data(username: str) -> dict:
    """Fetch user metrics from GitHub via GraphQL API."""
    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN environment variable is missing.")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    query = """
    query($login: String!, $from: DateTime!) {
      user(login: $login) {
        repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: STARGAZERS, direction: DESC}) {
          totalCount
          nodes {
            stargazerCount
            forkCount
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node {
                  name
                }
              }
            }
          }
        }
        contributionsCollection(from: $from) {
          totalCommitContributions
          totalPullRequestContributions
          totalIssueContributions
        }
        recentRepos: repositories(first: 1, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: OWNER) {
          nodes {
            pushedAt
          }
        }
      }
    }
    """

    # Calculate date 365 days ago
    from_date = (datetime.datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")

    variables = {
        "login": username,
        "from": from_date
    }

    logger.info(f"Fetching GraphQL data for user: {username}")
    session = get_session()

    try:
        response = session.post(
            GRAPHQL_ENDPOINT,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            logger.error(f"GraphQL errors: {json.dumps(data['errors'])}")
            sys.exit(1)

        user_data = data.get("data", {}).get("user")
        if not user_data:
            logger.error(f"User {username} not found or no access.")
            sys.exit(1)

        return user_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        sys.exit(1)

def process_stats(data: dict) -> dict:
    """Process GraphQL payload into concise statistics."""
    logger.info("Processing fetched statistics.")

    repos = data.get("repositories", {})
    repo_nodes = repos.get("nodes", [])

    # Core repo metrics
    total_repos = repos.get("totalCount", 0)
    total_stars = sum(r.get("stargazerCount", 0) for r in repo_nodes)
    total_forks = sum(r.get("forkCount", 0) for r in repo_nodes)

    # Contributions metrics
    contribs = data.get("contributionsCollection", {})
    total_commits = contribs.get("totalCommitContributions", 0)
    total_prs = contribs.get("totalPullRequestContributions", 0)
    total_issues = contribs.get("totalIssueContributions", 0)

    # Language metrics
    language_sizes = {}
    for r in repo_nodes:
        lang_edges = r.get("languages", {}).get("edges", [])
        for edge in lang_edges:
            name = edge["node"]["name"]
            size = edge["size"]
            language_sizes[name] = language_sizes.get(name, 0) + size

    # Sort and get top 5 languages
    total_bytes = sum(language_sizes.values())
    sorted_langs = sorted(language_sizes.items(), key=lambda x: x[1], reverse=True)[:5]

    top_languages = []
    for name, size in sorted_langs:
        percentage = (size / total_bytes * 100) if total_bytes > 0 else 0
        top_languages.append({"name": name, "percentage": percentage})

    # Recent activity
    recent_repos = data.get("recentRepos", {}).get("nodes", [])
    last_updated = "N/A"
    if recent_repos and "pushedAt" in recent_repos[0] and recent_repos[0]["pushedAt"]:
        pushed_at = recent_repos[0]["pushedAt"]
        dt = datetime.datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ")
        last_updated = dt.strftime("%B %d, %Y")
    else:
        last_updated = datetime.datetime.now(timezone.utc).strftime("%B %d, %Y")

    return {
        "total_repos": total_repos,
        "total_stars": total_stars,
        "total_forks": total_forks,
        "total_commits": total_commits,
        "total_prs": total_prs,
        "total_issues": total_issues,
        "top_languages": top_languages,
        "last_updated": last_updated
    }

def render_progress_bar(percentage: float, width: int = 20) -> str:
    """Generate a unicode progress bar."""
    filled = int((percentage / 100) * width)
    empty = width - filled
    return "█" * filled + "░" * empty

def render_markdown(stats: dict) -> str:
    """Render statistics into a terminal-style markdown block."""
    logger.info("Rendering markdown statistics.")

    lines = []

    # Core stats table
    lines.append("| Metric | Count |")
    lines.append("| :--- | :--- |")
    lines.append(f"| 📚 Public Repositories | {stats['total_repos']} |")
    lines.append(f"| ⭐ Total Stars | {stats['total_stars']} |")
    lines.append(f"| 🍴 Total Forks | {stats['total_forks']} |")
    lines.append(f"| 💻 Commits (Last 365 Days) | {stats['total_commits']} |")
    lines.append(f"| 🔄 Pull Requests (Last 365 Days) | {stats['total_prs']} |")
    lines.append(f"| 🐛 Issues Created (Last 365 Days) | {stats['total_issues']} |")
    lines.append("")

    # Languages section
    if stats["top_languages"]:
        lines.append("### 🏆 Top Languages")
        lines.append("```text")
        for lang in stats["top_languages"]:
            bar = render_progress_bar(lang['percentage'])
            name = lang['name'].ljust(12)
            pct = f"{lang['percentage']:.2f}%".rjust(7)
            lines.append(f"{name} {bar} {pct}")
        lines.append("```")
        lines.append("")

    # Timestamp
    lines.append(f"*(Last updated: {stats['last_updated']})*")

    return "\n".join(lines) + "\n"

def inject_readme(content: str) -> None:
    """Inject rendered markdown into the README.md file."""
    logger.info(f"Injecting content into {README_PATH}")

    try:
        with open(README_PATH, "r", encoding="utf-8") as f:
            readme_text = f.read()

        pattern = re.compile(r"(<!-- START_STATS -->\n).*?(\n<!-- END_STATS -->)", re.DOTALL)

        if not pattern.search(readme_text):
            logger.error("Could not find <!-- START_STATS --> and <!-- END_STATS --> markers in README.md")
            sys.exit(1)

        new_readme = pattern.sub(rf"\g<1>{content}\g<2>", readme_text)

        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(new_readme)

        logger.info("Successfully updated README.md")
    except FileNotFoundError:
        logger.error(f"File not found: {README_PATH}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error updating README: {e}")
        sys.exit(1)

def main():
    if not GITHUB_OWNER:
        logger.error("GITHUB_REPOSITORY_OWNER environment variable is missing.")
        sys.exit(1)

    data = fetch_graphql_data(GITHUB_OWNER)
    stats = process_stats(data)
    markdown_content = render_markdown(stats)
    inject_readme(markdown_content)

if __name__ == "__main__":
    main()
