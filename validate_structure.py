#!/usr/bin/env python3
"""
Validate that collect_data.py structure is correct without making API calls.
"""

# Simulate the queries and expected column order
Q = {
    # Copilot metrics
    "is:pr+head:copilot/": "copilot_total",
    "is:pr+head:copilot/+is:merged": "copilot_merged",
    "is:pr+head:copilot/+-is:draft": "copilot_nondraft",
    # Codex metrics
    "is:pr+head:codex/": "codex_total",
    "is:pr+head:codex/+is:merged": "codex_merged",
    "is:pr+head:codex/+-is:draft": "codex_nondraft",
    # Cursor metrics
    "is:pr+head:cursor/": "cursor_total",
    "is:pr+head:cursor/+is:merged": "cursor_merged",
    "is:pr+head:cursor/+-is:draft": "cursor_nondraft",
    # Devin metrics
    "author:devin-ai-integration[bot]": "devin_total",
    "author:devin-ai-integration[bot]+is:merged": "devin_merged",
    "author:devin-ai-integration[bot]+-is:draft": "devin_nondraft",
    # Codegen metrics
    "author:codegen-sh[bot]": "codegen_total",
    "author:codegen-sh[bot]+is:merged": "codegen_merged",
    "author:codegen-sh[bot]+-is:draft": "codegen_nondraft",
}

# Expected header from existing data.csv
expected_header = [
    "timestamp",
    "copilot_total",
    "copilot_merged",
    "codex_total",
    "codex_merged",
    "cursor_total",
    "cursor_merged",
    "devin_total",
    "devin_merged",
    "codegen_total",
    "codegen_merged",
    "copilot_nondraft",
    "codex_nondraft",
    "cursor_nondraft",
    "devin_nondraft",
    "codegen_nondraft",
]

# Row construction from script
row_keys = [
    "timestamp",
    "copilot_total",
    "copilot_merged",
    "codex_total",
    "codex_merged",
    "cursor_total",
    "cursor_merged",
    "devin_total",
    "devin_merged",
    "codegen_total",
    "codegen_merged",
    "copilot_nondraft",
    "codex_nondraft",
    "cursor_nondraft",
    "devin_nondraft",
    "codegen_nondraft",
]

print("🔍 Validation Results:")
print()

print("📋 Expected header order:")
for i, col in enumerate(expected_header):
    print(f"  {i+1:2d}. {col}")

print()
print("📝 Script row construction order:")
for i, col in enumerate(row_keys):
    print(f"  {i+1:2d}. {col}")

print()
print("✅ Order match check:")
if expected_header == row_keys:
    print("  ✓ PERFECT MATCH! Header and row construction are aligned.")
else:
    print("  ✗ MISMATCH! Need to fix alignment.")
    for i, (expected, actual) in enumerate(zip(expected_header, row_keys)):
        if expected != actual:
            print(f"    Position {i+1}: expected '{expected}', got '{actual}'")

print()
print("🔑 Query coverage check:")
query_keys = set(Q.values())
expected_keys = set(expected_header[1:])  # Exclude timestamp

missing_in_queries = expected_keys - query_keys
missing_in_expected = query_keys - expected_keys

if not missing_in_queries and not missing_in_expected:
    print("  ✓ ALL COLUMNS COVERED! Every expected column has a corresponding query.")
else:
    if missing_in_queries:
        print(f"  ✗ Missing queries for: {missing_in_queries}")
    if missing_in_expected:
        print(f"  ✗ Extra queries not in header: {missing_in_expected}")

print()
print("📊 Total queries:", len(Q))
print("📊 Total columns:", len(expected_header))
print()

if expected_header == row_keys and not missing_in_queries and not missing_in_expected:
    print("🎉 VALIDATION PASSED! The script structure is correct.")
else:
    print("❌ VALIDATION FAILED! Need to fix issues above.")
