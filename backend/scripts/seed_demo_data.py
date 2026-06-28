from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = PROJECT_ROOT / "data" / "demo"

SCENARIOS = {
    "nba_game": {
        "filename": "nba_game_comments.csv",
        "topic": "马刺 vs 尼克斯 G6 赛后讨论",
        "subjects": ["文班亚马", "布伦森", "主队后场", "客队锋线", "双方替补", "两队教练"],
        "positive": [
            "{subject}末节关键球执行很稳，连续两次挡拆都找到了最合理的机会。",
            "{subject}今天防守轮转太到位，协防和护框改变了比赛走势。",
            "这场团队进攻很流畅，转移球比前几场明显更快。",
            "暂停后的联防调整有效，第三节追回分差不是偶然。",
            "替补阵容贡献了真正的比赛强度，板凳奇兵值得表扬。",
            "最后五分钟双方球星都敢承担责任，这才是季后赛。",
        ],
        "neutral": [
            "从数据看，{subject}的得分不是最高，但正负值和篮板保护很关键。",
            "这场分差主要来自二次进攻，不应该只看最后一个回合。",
            "主队上半场打得更快，客队下半场通过阵地战把节奏压了下来。",
            "系列赛打到 G6，体能和轮换长度已经比单场手感更重要。",
            "回看第三节，双方都在针对中锋换防，战术选择有迹可循。",
            "补充一下，最后五分钟两队合计只有两次失误。",
        ],
        "negative": [
            "最后两分钟裁判判罚争议太大，{subject}那次防守看回放不像犯规。",
            "主队连续丢前场篮板，防守回合做了一半等于没做。",
            "{subject}今天手感低迷还一直浪投，关键阶段球权处理不合理。",
            "教练换人太慢，明显跑不动的阵容还在场上坚持了四分钟。",
            "边线球战术完全没跑出来，暂停回来出现这种失误不能接受。",
            "伤病影响了轮换，但防守漏人和沟通问题不能全怪伤病。",
        ],
    },
    "world_cup_game": {
        "filename": "world_cup_game_comments.csv",
        "topic": "阿根廷 vs 法国 世界杯淘汰赛讨论",
        "subjects": ["阿根廷中场", "法国边锋", "主队门将", "客队中卫", "双方替补", "两队教练"],
        "positive": [
            "{subject}高位压迫执行得很统一，开场就限制了对手出球。",
            "这次边路突破后的倒三角配合很漂亮，进球来自完整的战术设计。",
            "{subject}两次关键扑救保住了比分，门将表现是胜负手。",
            "防线造越位非常整齐，零封不是靠运气。",
            "替补上场后立刻提升攻防转换速度，这次换人效果明显。",
            "淘汰赛能踢出这种对攻节奏，比赛观赏性拉满。",
        ],
        "neutral": [
            "从射门分布看，{subject}控球更多，但真正进入禁区的机会并不多。",
            "上半场主队强调传控，下半场客队通过边路速度改变了局面。",
            "不要只看控球率，二点球和反击质量更能说明比赛走势。",
            "淘汰赛阶段体能分配很重要，双方最后二十分钟都主动降速。",
            "复盘这个丢球，问题从中场失位开始，不只是中卫一人的责任。",
            "补充数据：双方射正次数接近，门将处理拉开了差距。",
        ],
        "negative": [
            "这个点球判罚争议很大，VAR 回看没有消除球迷疑问。",
            "{subject}临门一脚太差，连续浪费两次单刀机会。",
            "防线回传失误太致命，淘汰赛不能给对手这种机会。",
            "中场下半场完全失控，拿不住球也组织不起有效反击。",
            "教练调整太晚，边路已经被打穿才想起换人。",
            "伤停确实影响阵容，但定位球漏人还是基本沟通问题。",
        ],
    },
}

TAILS = [
    "我更看重完整比赛过程。",
    "高赞不一定代表全部球迷。",
    "等官方数据和回放再判断。",
    "这一点在赛后讨论里分歧很大。",
    "别只用一个回合给整场表现下结论。",
]


def generate_demo_data(scenario: str = "all", rows_per_scenario: int = 320) -> None:
    """Generate two reproducible Hupu-style sports datasets."""

    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    names = SCENARIOS.keys() if scenario == "all" else [scenario]
    for name in names:
        rows = build_rows(name, rows_per_scenario)
        path = DEMO_DIR / SCENARIOS[name]["filename"]
        write_csv(path, rows)
        print(f"Generated {len(rows)} rows: {path}")


def build_rows(scenario: str, count: int) -> list[dict[str, str | int]]:
    config = SCENARIOS[scenario]
    now = datetime(2026, 6, 25, 12, tzinfo=timezone.utc)
    buckets = ["positive", "neutral", "negative"]
    rows: list[dict[str, str | int]] = []
    for index in range(count):
        bucket = buckets[(index * 5 + index // 13) % len(buckets)]
        templates = config[bucket]
        subject = config["subjects"][(index * 7 + index // 9) % len(config["subjects"])]
        template = templates[(index * 11 + index // 5) % len(templates)]
        content = f"{template.format(subject=subject)} {TAILS[(index * 3 + index // 17) % len(TAILS)]}"
        comment_id = f"{scenario}-{index + 1:04d}"
        rows.append(
            {
                "id": comment_id,
                "platform": "hupu",
                "topic": config["topic"],
                "content": content,
                "author_hash": hashlib.sha1(f"{scenario}:hupu:{index}".encode("utf-8")).hexdigest()[:16],
                "like_count": (index * 37 + index // 7 * 11) % 900,
                "reply_count": (index * 13 + index // 19) % 80,
                "publish_time": (now - timedelta(minutes=index * 7)).isoformat(),
                "source_url": f"https://example.com/demo/hupu/{scenario}/{comment_id}",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str | int]]) -> None:
    fieldnames = ["id", "platform", "topic", "content", "author_hash", "like_count", "reply_count", "publish_time", "source_url"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed focused Hupu sports demo data.")
    parser.add_argument("--scenario", choices=[*SCENARIOS.keys(), "all"], default="all")
    parser.add_argument("--rows", type=int, default=320)
    args = parser.parse_args()
    generate_demo_data(args.scenario, args.rows)


if __name__ == "__main__":
    main()
