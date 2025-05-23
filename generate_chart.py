#!/usr/bin/env python3
# PR‑tracker: generates a chart from the collected PR data.
# deps: pandas, matplotlib

from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import datetime as dt
import re

def generate_chart(csv_file=None):
    # Default to data.csv if no file specified
    if csv_file is None:
        csv_file = Path("data.csv")

    # Ensure file exists
    if not csv_file.exists():
        print(f"Error: {csv_file} not found.")
        print("Run collect_data.py first to collect data.")
        return False

    # Create chart
    df = pd.read_csv(csv_file, parse_dates=["timestamp"], date_format="%Y‑%m‑%d %H:%M:%S")

    # Check if data exists
    if len(df) == 0:
        print("Error: No data found in CSV file.")
        return False

    fig, ax = plt.subplots(figsize=(10, 6))  # Increased figure size for better readability

    # Plot percentages
    copilot_line, = ax.plot(df.timestamp, df.copilot_approved/df.copilot_total*100, 'o-', markersize=8, label="Copilot")
    codex_line, = ax.plot(df.timestamp, df.codex_approved/df.codex_total*100, 's-', markersize=8, label="Codex")

    ax.set_ylabel("Approval %")

    # Make sure the y-axis has a reasonable range even with few data points
    if len(df) <= 2:
        ax.set_ylim([0, 100])

    # Get latest data for the labels
    latest = df.iloc[-1]

    # Add a text box with current totals in the top right corner
    textstr = (
        f"Current Totals (approved/total):\n"
        f"Copilot: {int(latest.copilot_approved):,}/{int(latest.copilot_total):,}\n"
        f"Codex: {int(latest.codex_approved):,}/{int(latest.codex_total):,}"
    )

    # Place textbox in top right corner
    props = dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8)
    ax.text(0.98, 0.98, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', horizontalalignment='right', bbox=props)

    # Add a regular legend
    ax.legend(loc='upper left')

    # Add a title
    ax.set_title("PR Approval Rates")

    fig.autofmt_xdate()
    fig.tight_layout()

    # Save chart
    chart_file = Path("chart.png")
    fig.savefig(chart_file, dpi=140)
    print(f"Chart generated: {chart_file}")

    # Update the README with latest statistics
    update_readme(df)

    return True

def update_readme(df):
    """Update the README.md with the latest statistics"""
    readme_path = Path("README.md")

    # Skip if README doesn't exist
    if not readme_path.exists():
        print(f"Warning: {readme_path} not found, skipping README update.")
        return False

    # Get the latest data
    latest = df.iloc[-1]

    # Calculate approval rates
    copilot_rate = (latest.copilot_approved / latest.copilot_total * 100)
    codex_rate = (latest.codex_approved / latest.codex_total * 100)

    # Format numbers with commas
    copilot_total = f"{latest.copilot_total:,}"
    copilot_approved = f"{latest.copilot_approved:,}"
    codex_total = f"{latest.codex_total:,}"
    codex_approved = f"{latest.codex_approved:,}"

    # Create the new table content
    table_content = f"""## Current Statistics

| Project | Total PRs | Approved PRs | Approval Rate |
| ------- | --------- | ------------ | ------------- |
| Copilot | {copilot_total} | {copilot_approved} | {copilot_rate:.2f}% |
| Codex   | {codex_total} | {codex_approved} | {codex_rate:.2f}% |"""

    # Read the current README content
    readme_content = readme_path.read_text()

    # Split content at the statistics header (if it exists)
    if "## Current Statistics" in readme_content:
        base_content = readme_content.split("## Current Statistics")[0].rstrip()
        new_content = f"{base_content}\n\n{table_content}"
    else:
        new_content = f"{readme_content}\n\n{table_content}"

    # Write the updated content back
    readme_path.write_text(new_content)
    print(f"README.md updated with latest statistics.")
    return True

if __name__ == "__main__":
    generate_chart()
