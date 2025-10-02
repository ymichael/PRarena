#!/usr/bin/env python3
# PR‑tracker: generates a combo chart from the collected PR data.
# deps: pandas, matplotlib, numpy

from pathlib import Path
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt
import re
import json
from jinja2 import Environment, FileSystemLoader


TEMPLATE_DIR = Path("templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
env.filters["comma"] = lambda v: f"{int(v):,}" if isinstance(v, (int, float)) else v

AGENTS = [
    {
        "key": "copilot",
        "display": "Copilot",
        "long_name": "GitHub Copilot coding agent",
        "color": "#2563eb",
        "colors": {"total": "#93c5fd", "merged": "#2563eb", "line": "#1d4ed8"},
        "marker": "o",
        "annotation_offset": (0, 15),
        "info_url": "https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent",
        "total_query_url": "https://github.com/search?q=is:pr+head:copilot/&type=pullrequests",
        "merged_query_url": "https://github.com/search?q=is:pr+head:copilot/+is:merged&type=pullrequests",
        "ready_query_url": "https://github.com/search?q=is:pr+head:copilot/+-is:draft&type=pullrequests",
        "draft_query_url": "https://github.com/search?q=is:pr+head:copilot/+is:draft&type=pullrequests",
    },
    {
        "key": "codex",
        "display": "Codex",
        "long_name": "OpenAI Codex",
        "color": "#dc2626",
        "colors": {"total": "#fca5a5", "merged": "#dc2626", "line": "#b91c1c"},
        "marker": "s",
        "annotation_offset": (0, -20),
        "info_url": "https://openai.com/index/introducing-codex/",
        "total_query_url": "https://github.com/search?q=is:pr+head:codex/&type=pullrequests",
        "merged_query_url": "https://github.com/search?q=is:pr+head:codex/+is:merged&type=pullrequests",
        "ready_query_url": "https://github.com/search?q=is:pr+head:codex/+-is:draft&type=pullrequests",
        "draft_query_url": "https://github.com/search?q=is:pr+head:codex/+is:draft&type=pullrequests",
    },
    {
        "key": "cursor",
        "display": "Cursor",
        "long_name": "Cursor Agents",
        "color": "#7c3aed",
        "colors": {"total": "#c4b5fd", "merged": "#7c3aed", "line": "#6d28d9"},
        "marker": "d",
        "annotation_offset": (0, -35),
        "info_url": "https://docs.cursor.com/background-agent",
        "total_query_url": "https://github.com/search?q=is:pr+head:cursor/&type=pullrequests",
        "merged_query_url": "https://github.com/search?q=is:pr+head:cursor/+is:merged&type=pullrequests",
        "ready_query_url": "https://github.com/search?q=is:pr+head:cursor/+-is:draft&type=pullrequests",
        "draft_query_url": "https://github.com/search?q=is:pr+head:cursor/+is:draft&type=pullrequests",
    },
    {
        "key": "devin",
        "display": "Devin",
        "long_name": "Devin",
        "color": "#059669",
        "colors": {"total": "#86efac", "merged": "#059669", "line": "#047857"},
        "marker": "^",
        "annotation_offset": (0, -50),
        "info_url": "https://devin.ai/pricing",
        "total_query_url": "https://github.com/search?q=is:pr+author:devin-ai-integration[bot]&type=pullrequests",
        "merged_query_url": "https://github.com/search?q=is:pr+author:devin-ai-integration[bot]+is:merged&type=pullrequests",
        "ready_query_url": "https://github.com/search?q=is:pr+author:devin-ai-integration[bot]+-is:draft&type=pullrequests",
        "draft_query_url": "https://github.com/search?q=is:pr+author:devin-ai-integration[bot]+is:draft&type=pullrequests",
    },
    {
        "key": "codegen",
        "display": "Codegen",
        "long_name": "Codegen",
        "color": "#d97706",
        "colors": {"total": "#fed7aa", "merged": "#d97706", "line": "#b45309"},
        "marker": "v",
        "annotation_offset": (0, -65),
        "info_url": "https://codegen.com/",
        "total_query_url": "https://github.com/search?q=is:pr+author:codegen-sh[bot]&type=pullrequests",
        "merged_query_url": "https://github.com/search?q=is:pr+author:codegen-sh[bot]+is:merged&type=pullrequests",
        "ready_query_url": "https://github.com/search?q=is:pr+author:codegen-sh[bot]+-is:draft&type=pullrequests",
        "draft_query_url": "https://github.com/search?q=is:pr+author:codegen-sh[bot]+is:draft&type=pullrequests",
    },
    {
        "key": "terragon",
        "display": "Terragon Labs",
        "long_name": "Terragon Labs",
        "color": "#0ea5e9",
        "colors": {"total": "#bae6fd", "merged": "#0284c7", "line": "#0ea5e9"},
        "marker": "P",
        "annotation_offset": (0, -80),
        "info_url": "https://terragonlabs.com/",
        "total_query_url": "https://github.com/search?q=is:pr+head:terragon/&type=pullrequests",
        "merged_query_url": "https://github.com/search?q=is:pr+head:terragon/+is:merged&type=pullrequests",
        "ready_query_url": "https://github.com/search?q=is:pr+head:terragon/+-is:draft&type=pullrequests",
        "draft_query_url": "https://github.com/search?q=is:pr+head:terragon/+is:draft&type=pullrequests",
    },
]


def build_stats(latest, df=None):
    stats = {}

    def as_int(value, fallback=0):
        if pd.isna(value):
            return fallback
        return int(value)

    for agent in AGENTS:
        key = agent["key"]
        total = as_int(latest.get(f"{key}_total"), 0)
        merged = as_int(latest.get(f"{key}_merged"), 0)
        nondraft = as_int(latest.get(f"{key}_nondraft"), total)

        total_rate = (merged / total * 100) if total > 0 else 0
        ready_rate = (merged / nondraft * 100) if nondraft > 0 else 0

        stats[key] = {
            "total": total,
            "merged": merged,
            "nondraft": nondraft,
            "rate": ready_rate,
            "total_rate": total_rate,
            "ready_rate": ready_rate,
        }
    return stats


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
    df = pd.read_csv(csv_file)
    # Fix timestamp format - replace special dash characters with regular hyphens
    df["timestamp"] = df["timestamp"].str.replace("‑", "-")
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Check if data exists
    if len(df) == 0:
        print("Error: No data found in CSV file.")
        return False

    # Limit to 8 data points spread across the entire dataset to avoid chart getting too busy
    total_points = len(df)
    if total_points > 8:
        # Create evenly spaced indices across the entire dataset
        indices = np.linspace(0, total_points - 1, num=8, dtype=int)
        df = df.iloc[indices]
        print(
            f"Limited chart to 8 data points evenly distributed across {total_points} total points."
        )

    # Ensure metric columns exist for all agents (backward compatibility with older CSVs)
    for agent in AGENTS:
        key = agent["key"]
        for suffix in ("total", "merged", "nondraft"):
            column = f"{key}_{suffix}"
            if column not in df.columns:
                df[column] = 0
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).astype(int)

        merged_col = f"{key}_merged"
        nondraft_col = f"{key}_nondraft"
        total_col = f"{key}_total"

        ready_rate = (df[merged_col] / df[nondraft_col].replace(0, np.nan) * 100).fillna(0)
        total_rate = (df[merged_col] / df[total_col].replace(0, np.nan) * 100).fillna(0)

        df[f"{key}_percentage"] = ready_rate
        df[f"{key}_total_percentage"] = total_rate

    # Adjust chart size based on data points, adding extra space for legends
    num_points = len(df)
    if num_points <= 3:
        fig_width = max(12, num_points * 4)  # Increased from 10 to 12
        fig_height = 8  # Increased from 6 to 8
    else:
        fig_width = 16  # Increased from 14 to 16
        fig_height = 10  # Increased from 8 to 10

    # Create the combination chart
    fig, ax1 = plt.subplots(figsize=(fig_width, fig_height))
    ax2 = ax1.twinx()

    # Prepare data
    x = np.arange(len(df))
    num_agents = len(AGENTS)
    width = min(0.12, 0.8 / max(1, num_agents))
    offsets = (
        np.linspace(-(num_agents - 1) / 2, (num_agents - 1) / 2, num_agents)
        if num_agents > 1
        else np.array([0])
    )

    bar_containers = []
    for offset, agent in zip(offsets, AGENTS):
        key = agent["key"]
        positions = x + offset * width
        bars_total = ax1.bar(
            positions,
            df[f"{key}_total"],
            width,
            label=f"{agent['display']} Total",
            alpha=0.7,
            color=agent["colors"]["total"],
        )
        bars_merged = ax1.bar(
            positions,
            df[f"{key}_merged"],
            width,
            label=f"{agent['display']} Merged",
            alpha=1.0,
            color=agent["colors"]["merged"],
        )
        bar_containers.extend([bars_total, bars_merged])

    # Line charts for percentages (on secondary y-axis)
    for agent in AGENTS:
        key = agent["key"]
        ax2.plot(
            x,
            df[f"{key}_percentage"],
            f"{agent['marker']}-",
            color=agent["colors"]["line"],
            linewidth=3,
            markersize=10,
            label=f"{agent['display']} Success %",
            markerfacecolor="white",
            markeredgewidth=2,
            markeredgecolor=agent["colors"]["line"],
        )

    # Customize the chart
    ax1.set_xlabel("Data Points", fontsize=12, fontweight="bold")
    ax1.set_ylabel(
        "PR Counts (Total & Merged)", fontsize=12, fontweight="bold", color="black"
    )
    ax2.set_ylabel(
        "Merge Success Rate (%)", fontsize=12, fontweight="bold", color="black"
    )

    title = "PR Analytics: Volume vs Success Rate Comparison"
    ax1.set_title(title, fontsize=16, fontweight="bold", pad=20)

    # Set x-axis labels with timestamps
    timestamps = df["timestamp"].dt.strftime("%m-%d %H:%M")
    ax1.set_xticks(x)
    ax1.set_xticklabels(timestamps, rotation=45)

    # Add legends - move name labels to top left, success % labels to bottom right
    # Position legends further outside with more padding
    legend1 = ax1.legend(loc="upper left", bbox_to_anchor=(-0.15, 1.15))
    legend2 = ax2.legend(loc="lower right", bbox_to_anchor=(1.15, -0.15))

    # Add grid
    ax1.grid(True, alpha=0.3, linestyle="--")

    # Set percentage axis range
    ax2.set_ylim(0, 100)

    # Add value labels on bars (with safety checks)
    def add_value_labels(ax, bars, format_str="{:.0f}"):
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                # Ensure the label fits within reasonable bounds
                label_text = format_str.format(height)
                if len(label_text) > 10:  # Truncate very long numbers
                    if height >= 1000:
                        label_text = f"{height/1000:.1f}k"
                    elif height >= 1000000:
                        label_text = f"{height/1000000:.1f}M"

                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height,
                    label_text,
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    fontweight="normal",
                    color="black",
                )

    for bars in bar_containers:
        add_value_labels(ax1, bars)

    # Add percentage labels on line points (with validation and skip 0.0%)
    for idx in range(len(df)):
        for agent in AGENTS:
            key = agent["key"]
            pct = df[f"{key}_percentage"].iat[idx]
            if pd.notna(pct) and pct > 0.0:
                offset_x, offset_y = agent.get("annotation_offset", (0, 12))
                ax2.annotate(
                    f"{pct:.1f}%",
                    (idx, pct),
                    textcoords="offset points",
                    xytext=(offset_x, offset_y),
                    ha="center",
                    fontsize=10,
                    fontweight="bold",
                    color=agent["colors"]["line"],
                )

    plt.tight_layout(pad=6.0)

    # Adjust subplot parameters to ensure legends fit entirely outside the chart
    plt.subplots_adjust(left=0.2, right=0.85, top=0.85, bottom=0.2)

    # Save chart to docs directory (single location for both README and GitHub Pages)
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)  # Ensure docs directory exists
    chart_file = docs_dir / "chart.png"
    dpi = 150 if num_points <= 5 else 300
    fig.savefig(chart_file, dpi=dpi, bbox_inches="tight", facecolor="white")
    print(f"Chart generated: {chart_file}")

    # Export chart data as JSON for interactive chart
    export_chart_data_json(df)

    # Update the README with latest statistics
    update_readme(df)

    # Update the GitHub Pages with latest statistics
    update_github_pages(df)

    return True


def export_chart_data_json(df):
    """Export chart data as JSON for interactive JavaScript chart"""
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)

    # Prepare data for Chart.js
    chart_data = {"labels": [], "datasets": []}

    # Format timestamps for labels
    for _, row in df.iterrows():
        timestamp = row["timestamp"]
        if isinstance(timestamp, str):
            timestamp = pd.to_datetime(timestamp)
        chart_data["labels"].append(timestamp.strftime("%m/%d %H:%M"))

    colors = {agent["key"]: agent["colors"] for agent in AGENTS}

    # Add bar datasets for totals and merged PRs
    for agent in AGENTS:
        agent_key = agent["key"]
        agent_label = agent["display"]
        # Process data to replace leading zeros with None (null in JSON)
        total_data = df[f"{agent_key}_total"].tolist()
        merged_data = df[f"{agent_key}_merged"].tolist()
        ready_percentage_data = df[f"{agent_key}_percentage"].tolist()
        total_percentage_data = df[f"{agent_key}_total_percentage"].tolist()

        # Find first non-zero total value index
        first_nonzero_idx = None
        for i, total in enumerate(total_data):
            if total > 0:
                first_nonzero_idx = i
                break

        # Replace leading zeros with None
        if first_nonzero_idx is not None:
            for i in range(first_nonzero_idx):
                total_data[i] = None
                merged_data[i] = None
                ready_percentage_data[i] = None
                total_percentage_data[i] = None

        # Total PRs
        chart_data["datasets"].append(
            {
                "label": f"{agent_label} Total",
                "type": "bar",
                "data": total_data,
                "backgroundColor": colors[agent_key]["total"],
                "borderColor": colors[agent_key]["total"],
                "borderWidth": 1,
                "yAxisID": "y",
                "order": 2,
            }
        )

        # Merged PRs
        chart_data["datasets"].append(
            {
                "label": f"{agent_label} Merged",
                "type": "bar",
                "data": merged_data,
                "backgroundColor": colors[agent_key]["merged"],
                "borderColor": colors[agent_key]["merged"],
                "borderWidth": 1,
                "yAxisID": "y",
                "order": 2,
            }
        )

        # Success rate line (ready PRs) - shown by default
        chart_data["datasets"].append(
            {
                "label": f"{agent_label} Success % (Ready)",
                "type": "line",
                "data": ready_percentage_data,
                "borderColor": colors[agent_key]["line"],
                "backgroundColor": "rgba(255, 255, 255, 0.8)",
                "borderWidth": 3,
                "pointRadius": 3,
                "pointHoverRadius": 5,
                "fill": False,
                "yAxisID": "y1",
                "order": 1,
                "rateType": "ready",
            }
        )

        # Success rate line (all PRs) - hidden by default
        chart_data["datasets"].append(
            {
                "label": f"{agent_label} Success % (All)",
                "type": "line",
                "data": total_percentage_data,
                "borderColor": colors[agent_key]["line"],
                "backgroundColor": "rgba(255, 255, 255, 0.8)",
                "borderWidth": 3,
                "pointRadius": 3,
                "pointHoverRadius": 5,
                "fill": False,
                "yAxisID": "y1",
                "order": 1,
                "hidden": True,  # Hidden by default
                "rateType": "total",
            }
        )

    # Write JSON file
    json_file = docs_dir / "chart-data.json"
    with open(json_file, "w") as f:
        json.dump(chart_data, f, indent=2)

    print(f"Chart data exported: {json_file}")
    return True


def update_readme(df):
    """Render README.md from template with latest statistics"""
    readme_path = Path("README.md")
    if not readme_path.exists():
        print(f"Warning: {readme_path} not found, skipping README update.")
        return False

    latest = df.iloc[-1]
    stats = build_stats(latest)

    context = {"agents": AGENTS, "stats": stats}
    content = env.get_template("readme_template.md").render(context)
    readme_path.write_text(content)
    print("README.md updated with latest statistics.")
    return True


def update_github_pages(df):
    """Render the GitHub Pages site from template with latest statistics"""
    index_path = Path("docs/index.html")
    if not index_path.exists():
        print(f"Warning: {index_path} not found, skipping GitHub Pages update.")
        return False

    latest = df.iloc[-1]
    stats = build_stats(latest)
    timestamp = dt.datetime.now().strftime("%B %d, %Y %H:%M UTC")

    # Simple context - just the essentials
    context = {"agents": AGENTS, "stats": stats, "timestamp": timestamp}

    content = env.get_template("index_template.html").render(context)
    index_path.write_text(content)
    print("GitHub Pages updated with latest statistics and enhanced analytics.")
    return True


if __name__ == "__main__":
    generate_chart()
