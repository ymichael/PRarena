#!/usr/bin/env python3
"""
ONE-TIME SCRIPT: Reconcile merged PR counts for codegen specifically using GitHub API.
Used to fix discrepancies in codegen merged data after data collection issues.
Updates only the codegen_merged column for rows where codegen data exists (starting from row 122).
Completed: Fixed codegen merged counts to match actual GitHub data.
"""

import csv
import datetime as dt
import time
import os
from pathlib import Path
import requests
import shutil
from typing import Dict

# GitHub API headers - include PAT if available
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "PR-Watcher"}
if github_token := os.getenv("GITHUB_TOKEN"):
    HEADERS["Authorization"] = f"token {github_token}"
    print("✅ Using GitHub PAT for authentication")
else:
    print("⚠️  No GitHub PAT found, using unauthenticated requests")

# Query for merged codegen PRs
MERGED_QUERY = "is:pr+author:codegen-sh[bot]+is:merged"


def parse_timestamp(timestamp_str: str) -> dt.datetime:
    """Parse CSV timestamp to datetime object."""
    return dt.datetime.strptime(timestamp_str.replace("‑", "-"), "%Y-%m-%d %H:%M:%S")


def format_github_date(timestamp: dt.datetime) -> str:
    """Format datetime for GitHub API (ISO format with UTC)."""
    return timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_merged_count(timestamp: dt.datetime) -> int:
    """Get count of merged PRs for codegen up to the given timestamp."""
    github_time = format_github_date(timestamp)
    query = f"{MERGED_QUERY}+created:<{github_time}"

    try:
        response = requests.get(
            f"https://api.github.com/search/issues?q={query}",
            headers=HEADERS,
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("total_count", 0)
        elif response.status_code == 403:
            print(f"  Rate limited, waiting 20 seconds...")
            time.sleep(20)
            return get_merged_count(timestamp)  # Retry
        else:
            print(f"  Error {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"  Request failed: {e}")
        return None


def create_backup():
    """Create a backup of the current data.csv"""
    backup_path = Path("data_merged_backup.csv")
    shutil.copy2("data.csv", backup_path)
    print(f"✅ Backup created: {backup_path}")


def main():
    print("🔄 Starting codegen merged PR reconciliation...")

    # Create backup
    create_backup()

    # Read the current data
    rows = []
    with open("data.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    print(f"📊 Total rows: {len(rows)}")

    # Find codegen_merged column index
    try:
        codegen_merged_idx = header.index("codegen_merged")
        codegen_total_idx = header.index("codegen_total")
        timestamp_idx = header.index("timestamp")
    except ValueError as e:
        print(f"❌ Column not found: {e}")
        return

    # Find rows where codegen data exists (codegen_total > 0)
    codegen_rows = []
    for i, row in enumerate(rows):
        if int(row[codegen_total_idx]) > 0:
            codegen_rows.append(i)

    print(
        f"🎯 Found {len(codegen_rows)} rows with codegen data (starting from row {codegen_rows[0] + 2})"
    )

    # Track differences
    differences = []

    # Process each row with codegen data
    for i, row_idx in enumerate(codegen_rows):
        row = rows[row_idx]
        timestamp_str = row[timestamp_idx]
        old_merged = int(row[codegen_merged_idx])

        print(
            f"Processing {i+1}/{len(codegen_rows)}: {timestamp_str} (old merged: {old_merged})",
            end="",
        )

        try:
            timestamp = parse_timestamp(timestamp_str)
            new_merged = get_merged_count(timestamp)

            if new_merged is not None:
                if new_merged != old_merged:
                    differences.append(
                        {
                            "row": row_idx + 2,  # +2 for header and 0-indexing
                            "timestamp": timestamp_str,
                            "old_merged": old_merged,
                            "new_merged": new_merged,
                            "difference": new_merged - old_merged,
                        }
                    )
                    print(f" → {new_merged} (diff: {new_merged - old_merged:+d})")
                else:
                    print(f" → {new_merged} (no change)")

                # Update the row
                row[codegen_merged_idx] = str(new_merged)
            else:
                print(" → API error, skipping")

        except Exception as e:
            print(f" → Error: {e}")

        # Rate limiting delay
        time.sleep(1)

    # Write updated data back
    with open("data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"\n✅ Reconciliation complete!")
    print(f"📈 Updated {len(codegen_rows)} codegen rows")

    # Report differences
    if differences:
        print(f"\n📊 Found {len(differences)} differences:")
        for diff in differences:
            print(f"  Row {diff['row']}: {diff['timestamp']}")
            print(
                f"    Old: {diff['old_merged']}, New: {diff['new_merged']}, Diff: {diff['difference']:+d}"
            )
    else:
        print("\n✅ No differences found - all merged counts were already accurate!")


if __name__ == "__main__":
    main()
