#!/usr/bin/env python3
# PR‑tracker: generates a chart from the collected PR data.
# deps: pandas, matplotlib

from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt

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

    fig, ax = plt.subplots()
    ax.plot(df.timestamp, df.copilot_approved/df.copilot_total*100, 'o-', markersize=8, label="Copilot")
    ax.plot(df.timestamp, df.codex_approved/df.codex_total*100, 's-', markersize=8, label="Codex")
    ax.set_ylabel("approval %")
    ax.legend()

    # Make sure the y-axis has a reasonable range even with few data points
    if len(df) <= 2:
        ax.set_ylim([0, 100])

    fig.autofmt_xdate()
    fig.tight_layout()

    # Save chart
    chart_file = Path("chart.png")
    fig.savefig(chart_file, dpi=140)
    print(f"Chart generated: {chart_file}")
    return True

if __name__ == "__main__":
    generate_chart()
