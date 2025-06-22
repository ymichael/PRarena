### PR Analytics: Volume vs Success Rate (auto-updated)

View the [interactive dashboard](https://aavetis.github.io/ai-pr-watcher/) for these statistics.

## Data sources

Explore the GitHub search queries used:

{% for agent in agents %}

- **All {{ agent.display }} PRs**: [{{ agent.total_query_url }}]({{ agent.total_query_url }})
- **Merged {{ agent.display }} PRs**: [{{ agent.merged_query_url }}]({{ agent.merged_query_url }})
  {% endfor %}

---

![chart](docs/chart.png)

## Current Statistics

| Project | Total PRs | Merged PRs | Merge Rate |
| ------- | --------- | ---------- | ---------- |{%- for agent in agents %}
| {{ agent.display }} | {{ stats[agent.key].total | comma }} | {{ stats[agent.key].merged | comma }} | {{ stats[agent.key].rate | round(2) }}% |{%- endfor %}
