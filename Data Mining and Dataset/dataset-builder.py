"""
Combined Script to Generate a Dataset for Issue Recommendation

For each repository in a provided list, this script will:
  1. Build an intermediate JSON file (caching to avoid duplicate GitHub API calls)
     that maps issues to linked PRs and gathers:
       - Issue details (title, body, comments, labels, state, timestamps, opener)
       - For each linked PR: basic info, file changes (with diff patches), commit messages, and contributors
  2. Generate a CSV dataset where each row corresponds to a contributor–issue pair.
     The CSV includes repo name, contributor_id, issue metadata, linked PR count,
     concatenated file changes, and commit messages.

Configuration:
  - Set your GitHub access token.
  - Set your list of repositories (format: "owner/repo").
  - The script writes intermediate JSON files in the "cache" directory.
  - The diff patch newlines are replaced by "|;|".
"""

import csv
import json
import os
import re

from github import Github

# -------------------------- Configuration --------------------------
GITHUB_TOKEN = "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"  # Replace with your token
REPO_LIST = [
    "tensorflow/tensorflow",
    "numpy/numpy",
    # Add more repositories as needed
]
MAX_PRS = 500  # Maximum number of PRs to process per repository
CSV_OUTPUT = "dataset.csv"
CACHE_DIR = "cache"

# Delimiters for concatenating strings
COMMENT_DELIMITER = " || "
FILE_CHANGE_DELIMITER = " || "
COMMIT_MSG_DELIMITER = " || "
PATCH_NEWLINE_DELIMITER = "|;|"

# -------------------------- Utility Functions --------------------------
def sanitize_repo_name(repo_name):
    """Sanitize repo name for use in filenames."""
    return repo_name.replace("/", "_")

# -------------------------- GitHub Data Fetching Functions --------------------------
def get_issue_details(repo, issue_number):
    """Fetch issue details including body, comments, labels, state, timestamps, and opener."""
    try:
        issue = repo.get_issue(number=issue_number)
        body = issue.body if issue.body else ""
        comments = [comment.body for comment in issue.get_comments()]
        combined_comments = COMMENT_DELIMITER.join(comments)
        issue_state = issue.state
        created_at = issue.created_at.isoformat() if issue.created_at else ""
        closed_at = issue.closed_at.isoformat() if issue.closed_at else ""
        opened_by = issue.user.login if issue.user else ""
        labels = [label.name for label in issue.labels]
        combined_labels = ", ".join(labels)
        return {
            "body": body,
            "comments": combined_comments,
            "state": issue_state,
            "created_at": created_at,
            "closed_at": closed_at,
            "opened_by": opened_by,
            "labels": combined_labels
        }
    except Exception as e:
        print(f"Error fetching details for issue #{issue_number}: {e}")
        return {
            "body": "",
            "comments": "",
            "state": "",
            "created_at": "",
            "closed_at": "",
            "opened_by": "",
            "labels": ""
        }

def fetch_pr_file_changes(repo, pr_number):
    """Fetch file changes (including diff patch) for a given PR."""
    try:
        pr = repo.get_pull(pr_number)
        file_changes = []
        for f in pr.get_files():
            file_changes.append({
                "filename": f.filename,
                "additions": f.additions,
                "deletions": f.deletions,
                "changes": f.changes,
                "status": f.status,
                # Replace newlines in patch with "|;;;|" for CSV compatibility.
                "patch": f.patch.replace("\n", PATCH_NEWLINE_DELIMITER) if f.patch else ""
            })
        return file_changes
    except Exception as e:
        print(f"Error fetching file changes for PR #{pr_number}: {e}")
        return []

def fetch_commit_messages(repo, pr_number):
    """Fetch commit messages for a given PR."""
    try:
        pr = repo.get_pull(pr_number)
        messages = [commit.commit.message for commit in pr.get_commits()]
        return COMMIT_MSG_DELIMITER.join(messages)
    except Exception as e:
        print(f"Error fetching commit messages for PR #{pr_number}: {e}")
        return ""

def get_pr_contributors(repo, pr_number):
    """Fetch unique contributor usernames from commit authors of a PR."""
    try:
        pr = repo.get_pull(pr_number)
        contributors = set()
        for commit in pr.get_commits():
            if commit.author and commit.author.login:
                contributors.add(commit.author.login)
        return list(contributors)
    except Exception as e:
        print(f"Error fetching contributors for PR #{pr_number}: {e}")
        return []

def format_file_changes(pr_number, file_changes):
    """
    Format file changes into a string.
    Each entry: "PR#<pr_number> - file_path: diff_content"
    Multiple entries are separated by FILE_CHANGE_DELIMITER.
    """
    formatted = []
    for change in file_changes:
        filename = change.get("filename", "")
        patch = change.get("patch", "")
        formatted.append(f"PR#{pr_number} - {filename}: {patch}")
    return FILE_CHANGE_DELIMITER.join(formatted)

# -------------------------- Intermediate Data Generation --------------------------
def build_issue_solver_data(repo, max_prs=500):
    """
    Process a repository to map merged PRs to referenced issues and gather additional details.
    Returns a dictionary mapping issue numbers (as strings) to issue data.
    """
    # Step 1: Build PR to Issue Mapping
    pr_issue_mapping = {}
    processed_count = 0
    merged_prs = repo.get_pulls(state='closed', sort='updated', direction='desc')

    # Regex patterns for detecting issue references (e.g., "fixes #123")
    closing_patterns = [
        r'(?:close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)[\s:]+#(\d+)',
        r'(?:issue|issues)[\s:]+#(\d+)'
    ]

    for pr in merged_prs:
        try:
            if not pr.merged:
                continue
            processed_count += 1
            pr_info = {
                "number": pr.number,
                "title": pr.title,
                "author": pr.user.login,
                "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                "merged_by": pr.merged_by.login if pr.merged_by else None,
                "referenced_issues": []
            }
            if pr.body:
                for pattern in closing_patterns:
                    matches = re.findall(pattern, pr.body.lower())
                    for match in matches:
                        issue_number = int(match)
                        pr_info["referenced_issues"].append(issue_number)
            if pr_info["referenced_issues"]:
                pr_issue_mapping[pr.number] = pr_info
            if processed_count >= max_prs:
                break
        except Exception as e:
            print(f"Error processing PR #{pr.number}: {e}")
            continue

    # Step 2: Build Issue-Centric Mapping
    issue_solver_data = {}
    for pr_number, pr_data in pr_issue_mapping.items():
        for issue_number in pr_data["referenced_issues"]:
            if issue_number not in issue_solver_data:
                issue_solver_data[issue_number] = {
                    "issue_number": issue_number,
                    "title": None,      # To be updated with GitHub issue title
                    "linked_prs": [],
                    "solvers": set(),   # Using set to avoid duplicates
                    "file_changes": [],
                    "commit_messages": ""
                }
            # Append PR info
            issue_solver_data[issue_number]["linked_prs"].append({
                "number": pr_data["number"],
                "title": pr_data["title"],
                "merged_at": pr_data["merged_at"],
                "merged_by": pr_data["merged_by"],
            })

    # Step 3: Enrich Issue Data with GitHub details and linked PR details
    for issue_number in list(issue_solver_data.keys()):
        try:
            issue = repo.get_issue(issue_number)
            issue_solver_data[issue_number].update({
                "title": issue.title,
                "labels": [label.name for label in issue.labels],
                "state": issue.state,
                "created_at": issue.created_at.isoformat() if issue.created_at else "",
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else "",
                "opened_by": issue.user.login if issue.user else ""
            })
        except Exception as e:
            print(f"Error fetching details for issue #{issue_number}: {e}")

        # For each linked PR, fetch file changes, commit messages, and contributors.
        for pr_info in issue_solver_data[issue_number]["linked_prs"]:
            pr_number = pr_info["number"]
            file_changes = fetch_pr_file_changes(repo, pr_number)
            formatted_changes = format_file_changes(pr_number, file_changes)
            pr_info["file_changes"] = formatted_changes

            commit_msgs = fetch_commit_messages(repo, pr_number)
            pr_info["commit_messages"] = commit_msgs

            solvers = get_pr_contributors(repo, pr_number)
            for solver in solvers:
                issue_solver_data[issue_number]["solvers"].add(solver)
            issue_solver_data[issue_number]["file_changes"].append(formatted_changes)
            issue_solver_data[issue_number]["commit_messages"] += (COMMIT_MSG_DELIMITER + commit_msgs) if commit_msgs else ""

        issue_solver_data[issue_number]["solvers"] = list(issue_solver_data[issue_number]["solvers"])

    return issue_solver_data

# -------------------------- CSV Generation --------------------------
def generate_csv_rows(issue_solver_data, repo, repo_name):
    """
    Generate CSV rows from the issue solver data for a given repository.
    Each row corresponds to a contributor-issue pair.
    """
    rows = []
    for issue_key, issue_data in issue_solver_data.items():
        linked_prs = issue_data.get("linked_prs", [])
        linked_pr_count = len(linked_prs)
        modified_files = FILE_CHANGE_DELIMITER.join(issue_data.get("file_changes", []))
        commit_messages = issue_data.get("commit_messages", "").lstrip(COMMIT_MSG_DELIMITER)
        # For each solver, create a row.
        solvers = issue_data.get("solvers", [])
        if not solvers:
            solvers = ["unknown"]
        # Fetch issue details using the repo object.
        issue_details = get_issue_details(repo, issue_data.get("issue_number", 0))
        for solver in solvers:
            row = {
                "repo_name": repo_name,
                "contributor_id": solver,
                "issue_id": issue_data.get("issue_number", ""),
                "issue_title": issue_data.get("title", ""),
                "issue_body": issue_details.get("body", ""),
                "issue_comments": issue_details.get("comments", ""),
                "issue_state": issue_data.get("state", ""),
                "issue_created_at": issue_data.get("created_at", ""),
                "issue_closed_at": issue_data.get("closed_at", ""),
                "opened_by": issue_data.get("opened_by", ""),
                "issue_labels": ", ".join(issue_data.get("labels", [])) if issue_data.get("labels", []) else "",
                "linked_pr_count": linked_pr_count,
                "modified_source_files": modified_files,
                "commit_messages": commit_messages
            }
            rows.append(row)
    return rows

# -------------------------- Main Pipeline --------------------------
def main():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    gh = Github(GITHUB_TOKEN)
    all_csv_rows = []

    for repo_name in REPO_LIST:
        print(f"Processing repository: {repo_name}")
        sanitized_name = sanitize_repo_name(repo_name)
        cache_file = os.path.join(CACHE_DIR, f"issue_solver_data_{sanitized_name}.json")

        if os.path.exists(cache_file):
            print(f"Loading cached data for {repo_name} from {cache_file}")
            with open(cache_file, "r", encoding="utf-8") as f:
                issue_solver_data = json.load(f)
        else:
            print(f"Fetching data for {repo_name} from GitHub API")
            try:
                repo = gh.get_repo(repo_name)
            except Exception as e:
                print(f"Error accessing repository {repo_name}: {e}")
                continue
            issue_solver_data = build_issue_solver_data(repo, MAX_PRS)
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(issue_solver_data, f, indent=2)

        try:
            repo = gh.get_repo(repo_name)
            csv_rows = generate_csv_rows(issue_solver_data, repo, repo_name)
            all_csv_rows.extend(csv_rows)
        except Exception as e:
            print(f"Error generating CSV rows for {repo_name}: {e}")

    fieldnames = [
        "repo_name",
        "contributor_id",
        "issue_id",
        "issue_title",
        "issue_body",
        "issue_comments",
        "issue_state",
        "issue_created_at",
        "issue_closed_at",
        "opened_by",
        "issue_labels",
        "linked_pr_count",
        "modified_source_files",
        "commit_messages"
    ]

    with open(CSV_OUTPUT, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_csv_rows:
            writer.writerow(row)

    print(f"Dataset CSV generated successfully as {CSV_OUTPUT}")

if __name__ == "__main__":
    main()
