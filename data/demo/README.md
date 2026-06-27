# Demo Datasets

This directory contains mock-first demo datasets for the public GitHub version of Cross-Platform Comment Insight Agent.

Each CSV has at least 300 rows and uses the normalized connector schema:

```text
id, platform, topic, content, author_hash, like_count, reply_count, publish_time, source_url
```

Datasets:

- `nba_draft_comments.csv`: NBA draft prospect debates, draft-order controversy, team fit, player template discussion.
- `iaa_game_comments.csv`: IAA game review mining around ad fatigue, retention blockers, performance issues, monetization pressure.
- `news_event_comments.csv`: News-event public opinion around information transparency, stance divergence, trust risk, and information needs.

Regenerate the datasets:

```bash
python backend/scripts/seed_demo_data.py
```

These files are synthetic sample data. They are designed for local demos, CI smoke tests, and documentation screenshots. They do not contain private user data.
