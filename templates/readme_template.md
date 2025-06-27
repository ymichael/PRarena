### PR Analytics: Volume vs Success Rate (auto-updated)

View the [interactive dashboard](https://aavetis.github.io/ai-pr-watcher/) for these statistics.

## Understanding the Metrics

Different AI coding agents follow different workflows when creating pull requests:

- **All PRs**: Every pull request created by an agent, including DRAFT PRs
- **Ready PRs**: Non-draft pull requests that are ready for review and merging
- **Merged PRs**: Pull requests that were successfully merged into the codebase

**Key workflow differences**: Some agents like **Codex** iterate privately and create ready PRs directly, resulting in very few drafts but high merge rates. Others like **Copilot** and **Codegen** create draft PRs first, encouraging public iteration before marking them ready for review.

The statistics below focus on **Ready PRs only** to fairly compare agents across different workflows, measuring each agent's ability to produce mergeable code regardless of whether they iterate publicly (with drafts) or privately.

## Data sources

Explore the GitHub search queries used:

{% for agent in agents %}

- **All {{ agent.display }} PRs**: [{{ agent.total_query_url }}]({{ agent.total_query_url }})
- **Merged {{ agent.display }} PRs**: [{{ agent.merged_query_url }}]({{ agent.merged_query_url }})
  {% endfor %}

---

![chart](docs/chart.png)

## Current Statistics

| Project | Ready PRs | Merged PRs | Success Rate |
| ------- | --------- | ---------- | ------------ |{%- for agent in agents %}
| {{ agent.display }} | {{ stats[agent.key].nondraft | comma }} | {{ stats[agent.key].merged | comma }} | {{ stats[agent.key].rate | round(2) }}% |{%- endfor %}
