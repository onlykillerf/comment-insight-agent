# Focused Sports Demo Data

The repository ships two synthetic, reproducible Hupu-style datasets:

- `nba_game_comments.csv`: 320 basketball comments around a single NBA playoff game.
- `world_cup_game_comments.csv`: 320 football comments around a single World Cup knockout match.

Each row contains `id`, `platform`, `topic`, `content`, `author_hash`, `like_count`, `reply_count`, `publish_time`, and `source_url`.

These files are synthetic and safe for local demos. They do not represent real users or real match results. Run `python backend/scripts/seed_demo_data.py --scenario all` to regenerate them.
