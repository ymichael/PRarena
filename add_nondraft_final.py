#!/usr/bin/env python3
"""
Add non-draft PR data to existing data.csv - Single optimized script.
This script strategically samples data points and handles GitHub API limitations properly.
"""

import csv
import datetime as dt
import time
from pathlib import Path
import requests
from typing import Dict

# GitHub API headers
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "PR-Watcher"}

# Non-draft queries (excluding drafts with -is:draft)
NONDRAFT_QUERIES = {
    "is:pr+head:copilot/+-is:draft": "copilot_nondraft",
    "is:pr+head:codex/+-is:draft": "codex_nondraft",
    "is:pr+head:cursor/+-is:draft": "cursor_nondraft",
    "author:devin-ai-integration[bot]+-is:draft": "devin_nondraft",
    "author:codegen-sh[bot]+-is:draft": "codegen_nondraft",
}


def parse_timestamp(timestamp_str: str) -> dt.datetime:
    """Parse CSV timestamp to datetime object."""
    return dt.datetime.strptime(timestamp_str.replace("‑", "-"), "%Y-%m-%d %H:%M:%S")


def format_github_date(timestamp: dt.datetime) -> str:
    """Format datetime for GitHub API (ISO format with UTC)."""
    return timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_single_query():
    """Test a single query to verify our approach works."""
    print("Testing single query...")
    test_query = "is:pr+head:copilot/+-is:draft"

    try:
        r = requests.get(
            f"https://api.github.com/search/issues?q={test_query}",
            headers=HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        total = r.json()["total_count"]
        print(f"✓ Test query successful: {test_query} -> {total} results")
        return True
    except Exception as e:
        print(f"✗ Test query failed: {e}")
        return False


def get_nondraft_counts_at_time(timestamp: dt.datetime) -> Dict[str, int]:
    """Get non-draft PR counts at a specific timestamp with proper error handling."""
    counts = {}
    created_before = format_github_date(timestamp)

    print(f"Querying for timestamp: {timestamp} (GitHub format: {created_before})")

    for query_base, key in NONDRAFT_QUERIES.items():
        # Add time filter - PRs created before this timestamp
        full_query = f"{query_base}+created:<{created_before}"

        print(f"  {key}: {full_query}")

        for attempt in range(3):  # Max 3 attempts
            try:
                r = requests.get(
                    f"https://api.github.com/search/issues?q={full_query}",
                    headers=HEADERS,
                    timeout=30,
                )

                if r.status_code == 403:
                    wait_time = 60 * (2**attempt)  # 60s, 120s, 240s
                    print(f"    Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                elif r.status_code == 422:
                    print(f"    Query syntax error for {key}, skipping")
                    counts[key] = 0
                    break

                r.raise_for_status()
                count = r.json()["total_count"]
                counts[key] = count
                print(f"    ✓ {key}: {count}")
                break

            except Exception as e:
                if attempt == 2:  # Last attempt
                    print(f"    ✗ Failed {key}: {e}")
                    counts[key] = 0
                else:
                    print(f"    Retry {attempt + 1} for {key}")

        # Rate limiting: wait between queries
        time.sleep(3)

    return counts


def interpolate_linear(
    start_val: int,
    end_val: int,
    start_time: dt.datetime,
    end_time: dt.datetime,
    target_time: dt.datetime,
) -> int:
    """Linear interpolation between two data points."""
    if start_time == end_time:
        return start_val

    ratio = (target_time - start_time).total_seconds() / (
        end_time - start_time
    ).total_seconds()
    return round(start_val + (end_val - start_val) * ratio)


def main():
    """Main function to process data with strategic sampling."""
    input_file = Path("data.csv")
    backup_file = Path("data_backup.csv")

    if not input_file.exists():
        print("❌ Error: data.csv not found!")
        return

    # Test API first
    if not test_single_query():
        print("❌ API test failed. Check your connection and try again.")
        return

    # Create backup of original data
    print(f"📋 Creating backup: {backup_file}")
    import shutil

    shutil.copy2(input_file, backup_file)
    print(f"✅ Backup created")

    print(f"📖 Reading {input_file}")

    # Read all data
    with input_file.open("r", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    total_rows = len(rows)
    print(f"📊 Found {total_rows} rows")

    # New fieldnames with non-draft columns
    new_fieldnames = fieldnames + list(NONDRAFT_QUERIES.values())

    # Strategic sampling: first, last, and every 20 rows
    sample_indices = [0]  # Always include first
    for i in range(20, total_rows, 20):
        sample_indices.append(i)
    if (total_rows - 1) not in sample_indices:
        sample_indices.append(total_rows - 1)  # Always include last

    print(f"🎯 Sampling {len(sample_indices)} points: {sample_indices}")

    # Get sample data
    sample_data = {}
    for i, idx in enumerate(sample_indices):
        row = rows[idx]
        timestamp = parse_timestamp(row["timestamp"])

        print(
            f"\n📡 Sample {i+1}/{len(sample_indices)}: Row {idx+1} ({row['timestamp']})"
        )

        try:
            counts = get_nondraft_counts_at_time(timestamp)
            sample_data[idx] = {"timestamp": timestamp, "counts": counts}
            print(f"✅ Sample complete")
        except Exception as e:
            print(f"❌ Sample failed: {e}")
            sample_data[idx] = {
                "timestamp": timestamp,
                "counts": {key: 0 for key in NONDRAFT_QUERIES.values()},
            }

        # Wait between samples
        if i < len(sample_indices) - 1:
            print("⏱️  Waiting 10 seconds...")
            time.sleep(10)

    print(f"\n💾 Writing updated data back to {input_file}")

    # Process all rows with interpolation
    with input_file.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()

        for idx in range(total_rows):
            row = rows[idx].copy()
            timestamp = parse_timestamp(row["timestamp"])

            if idx in sample_data:
                # Use actual sample data
                row.update(sample_data[idx]["counts"])
            else:
                # Interpolate between nearest samples
                prev_idx = max([i for i in sample_indices if i < idx])
                next_idx = min([i for i in sample_indices if i > idx])

                prev_data = sample_data[prev_idx]
                next_data = sample_data[next_idx]

                # Interpolate each metric
                for key in NONDRAFT_QUERIES.values():
                    interpolated = interpolate_linear(
                        prev_data["counts"][key],
                        next_data["counts"][key],
                        prev_data["timestamp"],
                        next_data["timestamp"],
                        timestamp,
                    )
                    row[key] = interpolated

            writer.writerow(row)

            if (idx + 1) % 50 == 0:
                print(f"  📝 Processed {idx + 1}/{total_rows} rows")

    print(f"\n✅ Complete! Updated {input_file} with non-draft data")
    print(f"📈 Added non-draft columns using {len(sample_indices)} API samples")
    print(f"💾 Original data backed up to {backup_file}")

    # Show sample of results
    print(f"\n📋 Sample results:")
    with input_file.open("r") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i < 3:  # Show first 3 rows
                print(
                    f"  Row {i+1}: copilot_nondraft={row['copilot_nondraft']}, codex_nondraft={row['codex_nondraft']}"
                )


if __name__ == "__main__":
    print("🚀 Adding non-draft PR data to data.csv")
    print(
        "This uses strategic sampling to minimize API calls while maintaining accuracy."
    )

    response = input("\nContinue? (y/N): ")
    if response.lower() == "y":
        main()
    else:
        print("Cancelled.")
