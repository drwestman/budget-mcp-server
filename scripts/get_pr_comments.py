#!/usr/bin/env python3
"""
Optimized PR Comments Fetcher
Combines shell script and Python functionality into a single file.
Optimized output format for LLM consumption.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from typing import Any


def run_gh_command(cmd: list[str]) -> dict[str, Any] | list[dict[str, Any]] | None:
    """Execute GitHub CLI command and return parsed JSON result."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        parsed_result = json.loads(result.stdout)
        return parsed_result  # type: ignore
    except subprocess.CalledProcessError as e:
        print(f"Error running GitHub CLI command: {' '.join(cmd)}", file=sys.stderr)
        print(f"Error: {e.stderr}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing GitHub CLI response: {e}", file=sys.stderr)
        return None


def get_repo_info() -> tuple[str, str] | None:
    """Get current repository owner and name."""
    # Get both owner and name in one call
    result = run_gh_command(["gh", "repo", "view", "--json", "owner,name"])

    if not result or not isinstance(result, dict):
        return None

    owner_login = result.get("owner", {}).get("login")
    repo_name = result.get("name")

    if not owner_login or not repo_name:
        return None

    return owner_login, repo_name


def get_current_pr_number() -> int | None:
    """Get current pull request number."""
    result = run_gh_command(["gh", "pr", "view", "--json", "number"])

    if result and isinstance(result, dict) and "number" in result:
        try:
            return int(result["number"])
        except (ValueError, TypeError):
            pass
    return None


def get_review_threads_graphql(
    owner: str, repo: str, pr_number: int
) -> dict[str, dict[str, Any]]:
    """Fetch review threads with resolution status using GraphQL."""
    graphql_query = """
    query($owner: String!, $repo: String!, $pr_number: Int!) {
      repository(owner: $owner, name: $repo) {
        pullRequest(number: $pr_number) {
          reviewThreads(first: 100) {
            nodes {
              id
              isResolved
              comments(first: 100) {
                nodes {
                  id
                  databaseId
                }
              }
            }
          }
        }
      }
    }
    """

    cmd = [
        "gh",
        "api",
        "graphql",
        "-f",
        f"query={graphql_query}",
        "-F",
        f"owner={owner}",
        "-F",
        f"repo={repo}",
        "-F",
        f"pr_number={pr_number}",
    ]

    result = run_gh_command(cmd)
    if not result or not isinstance(result, dict):
        return {}

    thread_mapping = {}
    try:
        review_threads = result["data"]["repository"]["pullRequest"]["reviewThreads"][
            "nodes"
        ]
        for thread in review_threads:
            thread_id = thread["id"]
            is_resolved = thread["isResolved"]

            for comment in thread["comments"]["nodes"]:
                comment_db_id = comment["databaseId"]
                thread_mapping[str(comment_db_id)] = {
                    "resolved": is_resolved,
                    "thread_id": thread_id,
                }
    except (KeyError, TypeError) as e:
        print(f"Warning: Error parsing GraphQL response: {e}", file=sys.stderr)

    return thread_mapping


def map_comment_resolution(
    comments_data: dict[str, list[dict[str, Any]]],
    thread_mapping: dict[str, dict[str, Any]],
) -> None:
    """Map resolution status to comments using thread mapping."""
    for comment_type in ["review_comments"]:
        for comment in comments_data[comment_type]:
            comment_id = str(comment.get("id", ""))
            if comment_id in thread_mapping:
                comment["resolved"] = thread_mapping[comment_id]["resolved"]
                comment["thread_id"] = thread_mapping[comment_id]["thread_id"]
            else:
                comment["resolved"] = None
                comment["thread_id"] = None


def fetch_all_pr_comments(
    owner: str, repo: str, pr_number: int
) -> dict[str, list[dict[str, Any]]]:
    """Fetch all types of PR comments and organize by type."""
    comments_data: dict[str, list[dict[str, Any]]] = {
        "issue_comments": [],
        "review_comments": [],
        "review_bodies": [],
    }

    # Fetch issue comments (general PR discussion)
    issue_comments = run_gh_command(
        [
            "gh",
            "api",
            f"/repos/{owner}/{repo}/issues/{pr_number}/comments",
            "--paginate",
        ]
    )
    if issue_comments and isinstance(issue_comments, list):
        comments_data["issue_comments"] = issue_comments

    # Fetch review comments (code-specific comments)
    review_comments = run_gh_command(
        ["gh", "api", f"/repos/{owner}/{repo}/pulls/{pr_number}/comments", "--paginate"]
    )
    if review_comments and isinstance(review_comments, list):
        comments_data["review_comments"] = review_comments

    # Fetch review bodies
    reviews = run_gh_command(
        ["gh", "api", f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews", "--paginate"]
    )
    if reviews and isinstance(reviews, list):
        # Filter reviews that have body content
        review_bodies = [
            review
            for review in reviews
            if (
                isinstance(review, dict)
                and review.get("body")
                and review["body"].strip()
            )
        ]
        comments_data["review_bodies"] = review_bodies

    # Fetch resolution status using GraphQL
    thread_mapping = get_review_threads_graphql(owner, repo, pr_number)

    # Map resolution status to comments
    map_comment_resolution(comments_data, thread_mapping)

    return comments_data


def format_comment_for_llm(comment: dict[str, Any], comment_type: str) -> str:
    """Format a single comment for optimal LLM readability."""
    lines = []

    # Header with metadata
    lines.append(f"COMMENT_TYPE: {comment_type}")
    lines.append(f"COMMENT_ID: {comment['id']}")
    lines.append(f"AUTHOR: {comment['user']['login']}")
    timestamp = comment.get("created_at", comment.get("submitted_at", "N/A"))
    lines.append(f"CREATED: {timestamp}")

    # Additional metadata for review comments
    if comment_type == "review_comment" and "path" in comment:
        lines.append(f"FILE: {comment['path']}")
        if "line" in comment:
            lines.append(f"LINE: {comment['line']}")
        if "diff_hunk" in comment:
            lines.append(f"DIFF_CONTEXT: {comment['diff_hunk']}")

    # Review state for review bodies
    if comment_type == "review_body" and "state" in comment:
        lines.append(f"REVIEW_STATE: {comment['state']}")

    # Resolution status for review comments
    if comment_type == "review_comment":
        resolved_status = comment.get("resolved")
        if resolved_status is not None:
            lines.append(f"RESOLVED: {str(resolved_status).lower()}")
            thread_id = comment.get("thread_id")
            if thread_id:
                lines.append(f"THREAD_ID: {thread_id}")
        else:
            lines.append("RESOLVED: unknown")

    lines.append(f"URL: {comment['html_url']}")
    lines.append("CONTENT_START")
    lines.append(comment.get("body", "").strip())
    lines.append("CONTENT_END")
    lines.append("=" * 80)

    return "\n".join(lines)


def display_comments_for_llm(
    owner: str,
    repo: str,
    pr_number: int,
    comments_data: dict[str, list[dict[str, Any]]],
    resolution_filter: str | None = None,
) -> None:
    """Display all comments in LLM-optimized format."""
    print("PULL_REQUEST_COMMENTS_START")
    print(f"REPOSITORY: {owner}/{repo}")
    print(f"PR_NUMBER: {pr_number}")
    print(f"FETCH_TIME: {datetime.now().isoformat()}")
    print("=" * 80)

    # Apply resolution filtering to review comments if specified
    filtered_review_comments = comments_data["review_comments"]
    if resolution_filter is not None:
        filtered_review_comments = []
        for comment in comments_data["review_comments"]:
            resolved_status = comment.get("resolved")
            if resolution_filter in ["resolved", "r"] and resolved_status is True:
                filtered_review_comments.append(comment)
            elif resolution_filter in ["unresolved", "u"] and resolved_status is False:
                filtered_review_comments.append(comment)

    # Combine all comments with timestamps for chronological sorting
    all_comments = []

    for comment in comments_data["issue_comments"]:
        all_comments.append((comment["created_at"], comment, "issue_comment"))

    for comment in filtered_review_comments:
        all_comments.append((comment["created_at"], comment, "review_comment"))

    for comment in comments_data["review_bodies"]:
        timestamp = comment.get("submitted_at", comment.get("created_at", ""))
        all_comments.append((timestamp, comment, "review_body"))

    # Sort chronologically
    def get_timestamp(comment_tuple: tuple[str, dict[str, Any], str]) -> str:
        return comment_tuple[0]

    all_comments.sort(key=get_timestamp)

    # Calculate resolution counts
    resolved_count = 0
    unresolved_count = 0
    unknown_count = 0

    for comment in comments_data["review_comments"]:
        resolved_status = comment.get("resolved")
        if resolved_status is True:
            resolved_count += 1
        elif resolved_status is False:
            unresolved_count += 1
        else:
            unknown_count += 1

    # Display counts
    print(f"TOTAL_COMMENTS: {len(all_comments)}")
    print(f"ISSUE_COMMENTS: {len(comments_data['issue_comments'])}")
    print(f"REVIEW_COMMENTS: {len(filtered_review_comments)}")
    print(f"REVIEW_BODIES: {len(comments_data['review_bodies'])}")
    print(f"RESOLVED_COMMENTS: {resolved_count}")
    print(f"UNRESOLVED_COMMENTS: {unresolved_count}")
    print(f"UNKNOWN_RESOLUTION: {unknown_count}")
    if resolution_filter is not None:
        print(f"RESOLUTION_FILTER: {resolution_filter}")
    print("=" * 80)

    if not all_comments:
        print("NO_COMMENTS_FOUND")
        print("=" * 80)
        print("PULL_REQUEST_COMMENTS_END")
        return

    # Display all comments chronologically
    for i, (timestamp, comment, comment_type) in enumerate(all_comments, 1):
        print(f"COMMENT_NUMBER: {i}")
        print(format_comment_for_llm(comment, comment_type))

    print("PULL_REQUEST_COMMENTS_END")


def main() -> None:
    """Main function with improved argument handling."""
    parser = argparse.ArgumentParser(
        description="Fetch and display PR comments optimized for LLM consumption"
    )
    parser.add_argument("--owner", help="GitHub repository owner")
    parser.add_argument("--repo", help="GitHub repository name")
    parser.add_argument("--pr_number", type=int, help="Pull Request number")
    parser.add_argument(
        "--resolution-filter",
        "-r",
        nargs="?",
        const="unresolved",
        choices=["resolved", "unresolved", "r", "u"],
        help="Filter review comments by resolution status. "
        "Default: show all comments. Use flag without value to show unresolved only. "
        "Options: 'resolved'/'r' for resolved, 'unresolved'/'u' for unresolved.",
    )

    args = parser.parse_args()

    # Auto-detect if not provided
    if not args.owner or not args.repo:
        repo_info = get_repo_info()
        if not repo_info:
            print(
                "Error: Could not determine repository info. "
                "Use --owner and --repo flags.",
                file=sys.stderr,
            )
            sys.exit(1)
        args.owner, args.repo = repo_info

    if not args.pr_number:
        pr_number = get_current_pr_number()
        if not pr_number:
            print(
                "Error: Could not determine current PR number. "
                "Use --pr_number flag.",
                file=sys.stderr,
            )
            sys.exit(1)
        args.pr_number = pr_number

    # Fetch and display comments
    comments_data = fetch_all_pr_comments(args.owner, args.repo, args.pr_number)
    display_comments_for_llm(
        args.owner, args.repo, args.pr_number, comments_data, args.resolution_filter
    )


if __name__ == "__main__":
    main()
