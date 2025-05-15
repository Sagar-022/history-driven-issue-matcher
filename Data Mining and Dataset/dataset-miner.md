
## Issue–Solver Dataset Miner

A minimal pipeline to mine GitHub repos for merged PRs and the issues they close, then emit a CSV of “contributor–issue” pairs with rich metadata (comments, labels, diffs, etc.).

## Prerequisites

- Python 3.8+  
- Install dependencies:
  ```bash
  pip install PyGithub

## Configuration

1. Open `dataset-builder.py`.
2. At the top, set:

   ```python
   GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"
   REPO_LIST     = ["owner1/repo1", "owner2/repo2", …]
   MAX_PRS       = 500
   CSV_OUTPUT    = "dataset.csv"
   ```
3. (Optional) Adjust delimiters if needed:

   ```python
   COMMENT_DELIMITER   = " || "
   FILE_CHANGE_DELIM   = " || "
   COMMIT_MSG_DELIM    = " || "
   PATCH_NEWLINE_DELIM = "|;|"
   ```

## Running

```bash
python dataset-builder.py
```

* **First run** writes intermediate JSON files under `cache/`.
* **Subsequent runs** will reuse that cache for speed.
* The final CSV appears at `dataset.csv`.

## Output

* **cache/issue\_solver\_data\_\<owner\_repo>.json** — raw mined data
* **dataset.csv** — one row per contributor–issue, with columns:

  ```
  repo_name, contributor_id, issue_id,
  issue_title, issue_body, issue_comments,
  issue_state, issue_created_at, issue_closed_at,
  opened_by, issue_labels, linked_pr_count,
  modified_source_files, commit_messages
  ```

```