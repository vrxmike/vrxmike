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
    """Fetch user metrics from GitHub via GraphQL API, with pagination for repositories."""
    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN environment variable is missing.")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    # First query to get user-level stats and the first page of repos
    user_query = """
    query($login: String!, $from: DateTime!, $cursor: String) {
      user(login: $login) {
        repositories(first: 100, after: $cursor, ownerAffiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER], orderBy: {field: STARGAZERS, direction: DESC}) {
          totalCount
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            isPrivate
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
          restrictedContributionsCount
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                color
              }
            }
          }
        }
        recentRepos: repositories(first: 1, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER]) {
          nodes {
            pushedAt
          }
        }
      }
    }
    """

    # Separate query for paginating through the remaining repos only
    repo_pagination_query = """
    query($login: String!, $cursor: String) {
      user(login: $login) {
        repositories(first: 100, after: $cursor, ownerAffiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER], orderBy: {field: STARGAZERS, direction: DESC}) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            isPrivate
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
      }
    }
    """

    from_date = (datetime.datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")

    logger.info(f"Fetching GraphQL data for user: {username}")
    session = get_session()

    # --- Fetch First Page & Core Stats ---
    variables = {
        "login": username,
        "from": from_date,
        "cursor": None
    }

    try:
        response = session.post(
            GRAPHQL_ENDPOINT,
            json={"query": user_query, "variables": variables},
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

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        sys.exit(1)

    # --- Handle Pagination for Repositories ---
    has_next_page = user_data["repositories"]["pageInfo"]["hasNextPage"]
    end_cursor = user_data["repositories"]["pageInfo"]["endCursor"]

    while has_next_page:
        logger.info(f"Paginating repositories, fetching after: {end_cursor}")
        variables = {
            "login": username,
            "cursor": end_cursor
        }

        try:
            response = session.post(
                GRAPHQL_ENDPOINT,
                json={"query": repo_pagination_query, "variables": variables},
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            page_data = response.json()

            if "errors" in page_data:
                logger.error(f"GraphQL pagination errors: {json.dumps(page_data['errors'])}")
                break

            repo_data = page_data.get("data", {}).get("user", {}).get("repositories", {})

            # Extend the nodes
            user_data["repositories"]["nodes"].extend(repo_data.get("nodes", []))

            has_next_page = repo_data.get("pageInfo", {}).get("hasNextPage", False)
            end_cursor = repo_data.get("pageInfo", {}).get("endCursor")

        except requests.exceptions.RequestException as e:
            logger.error(f"Pagination request failed: {e}")
            break

    return user_data

def process_stats(data: dict) -> dict:
    """Process GraphQL payload into concise statistics."""
    logger.info("Processing fetched statistics.")

    repos = data.get("repositories", {})
    repo_nodes = repos.get("nodes", [])

    # Core repo metrics
    total_repos = max(repos.get("totalCount", 0), len(repo_nodes))

    # Contributions metrics
    contribs = data.get("contributionsCollection", {})
    
    public_commits = contribs.get("totalCommitContributions", 0)
    restricted_contribs = contribs.get("restrictedContributionsCount", 0)
    total_commits = public_commits + restricted_contribs
    
    total_prs = contribs.get("totalPullRequestContributions", 0)
    total_issues = contribs.get("totalIssueContributions", 0)

    # ⚡ Bolt Optimization: Single-pass over repo_nodes
    # Reduces O(4N) iterations to O(N) by calculating stars, forks, languages, and private flag together.
    total_stars = 0
    total_forks = 0
    language_sizes = {}
    has_private = False

    for r in repo_nodes:
        total_stars += r.get("stargazerCount", 0)
        total_forks += r.get("forkCount", 0)

        if not has_private and r.get("isPrivate", False):
            has_private = True

        lang_edges = r.get("languages", {}).get("edges", [])
        for edge in lang_edges:
            name = edge["node"]["name"]
            if name == "Jupyter Notebook":
                continue
            language_sizes[name] = language_sizes.get(name, 0) + edge["size"]

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
        "last_updated": last_updated,
        "private_included": restricted_contribs > 0 or has_private
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
    lines.append(f"| 📚 Total Repositories | {stats['total_repos']} |")
    lines.append(f"| ⭐ Total Stars | {stats['total_stars']} |")
    lines.append(f"| 🍴 Total Forks | {stats['total_forks']} |")
    lines.append(f"| 💻 Total Commits | {stats['total_commits']} |")
    lines.append(f"| 🔄 Pull Requests | {stats['total_prs']} |")
    lines.append(f"| 🐛 Issues Created | {stats['total_issues']} |")
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

    # Timestamp and notice
    notice = " (inc. private)" if stats.get("private_included") else ""
    lines.append(f"*(Last updated: {stats['last_updated']}{notice})*")

    return "\n".join(lines) + "\n"

def generate_contribution_svg(calendar_data: dict) -> str:
    """Generate a GitHub-style heatmap SVG from calendar data."""
    logger.info("Generating contribution heatmap SVG.")
    
    # SVG Layout Constants
    SQUARE_SIZE = 10
    GAP = 2
    RADIUS = 2
    LEFT_PAD = 0
    TOP_PAD = 20
    
    rects = []
    
    # Iterate through weeks and days
    for w_idx, week in enumerate(calendar_data.get('weeks', [])):
        x = LEFT_PAD + (w_idx * (SQUARE_SIZE + GAP))
        for d_idx, day in enumerate(week.get('contributionDays', [])):
            y = TOP_PAD + (d_idx * (SQUARE_SIZE + GAP))
            color = day.get('color', '#ebedf0')
            count = day.get('contributionCount', 0)
            date = day.get('date', '')
            
            rect = (
                f'<rect width="{SQUARE_SIZE}" height="{SQUARE_SIZE}" '
                f'x="{x}" y="{y}" fill="{color}" rx="{RADIUS}" ry="{RADIUS}">'
                f'<title>{count} contributions on {date}</title>'
                f'</rect>'
            )
            rects.append(rect)

    width = (53 * (SQUARE_SIZE + GAP))
    height = TOP_PAD + (7 * (SQUARE_SIZE + GAP))
    
    svg_header = (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'fill="none" xmlns="http://www.w3.org/2000/svg">'
    )
    
    label = f'<text x="0" y="12" fill="#8b949e" font-size="10" font-family="sans-serif">Contribution Activity (inc. private)</text>'
    
    svg_content = "\n  ".join(rects)
    return f"{svg_header}\n  {label}\n  {svg_content}\n</svg>"

def inject_readme(content: str) -> None:
    """Inject rendered markdown into the README.md file."""
    logger.info(f"Injecting content into {README_PATH}")

    try:
        with open(README_PATH, "r", encoding="utf-8") as f:
            readme_text = f.read()

        pattern = re.compile(r"(<!-- START_STATS -->).*?(<!-- END_STATS -->)", re.DOTALL)

        if not pattern.search(readme_text):
            logger.error("Could not find <!-- START_STATS --> and <!-- END_STATS --> markers in README.md")
            sys.exit(1)

        # Safely inject with lambda instead of rf-strings
        new_readme = pattern.sub(lambda m: f"{m.group(1)}\n{content}{m.group(2)}", readme_text)

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
    
    # Generate and save SVG
    calendar = data.get("contributionsCollection", {}).get("contributionCalendar", {})
    if calendar:
        svg_content = generate_contribution_svg(calendar)
        with open("activity.svg", "w", encoding="utf-8") as f:
            f.write(svg_content)
        logger.info("Successfully saved activity.svg")

    markdown_content = render_markdown(stats)
    inject_readme(markdown_content)

if __name__ == "__main__":
    main()
