from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = PROJECT_ROOT / "data" / "demo"


SCENARIOS = {
    "nba_draft": {
        "filename": "nba_draft_comments.csv",
        "platforms": ["xhs", "weibo", "bili", "zhihu"],
        "topic": "2026 NBA Draft Opinion Analysis",
        "subjects": ["迪班萨", "皮特森", "布泽尔", "弗拉格", "AJ", "乐透锋线", "国际内线", "控卫新秀"],
        "positive": [
            "{subject}的身体模板确实稀缺，顺位高一点也能理解。",
            "看好{subject}，年龄小还有成长空间，球队如果愿意培养会很赚。",
            "{subject}投射和持球都比预期成熟，放在乐透末性价比不错。",
            "这个顺位选{subject}不亏，刚好适配球队缺锋线的需求。",
            "{subject}的话题热度高，媒体曝光能带动新秀关注度。",
            "国际球员这条线很有潜力，{subject}的FIBA经验不是空话。",
        ],
        "neutral": [
            "{subject}的样本还不够大，还是要等夏联和体测数据。",
            "我更关心球队培养环境，单看模板很容易高估{subject}。",
            "{subject}排在这个区间可以讨论，但别只看集锦下结论。",
            "现在榜单变动很快，{subject}后面还有联合试训。",
            "这个帖子把顺位和球队需求放一起看，比单纯排名有价值。",
            "补充一下，{subject}上赛季主要问题是角色变化太快。",
        ],
        "negative": [
            "{subject}对抗还是偏弱，进NBA第一年可能顶不住。",
            "担心{subject}横移速度，换防小后卫会被点名。",
            "{subject}投篮稳定性一般，样本联赛含金量也有争议。",
            "这个顺位选{subject}感觉过高，模板吹得有点太满。",
            "{subject}伤病风险不能忽视，球队要有耐心才行。",
            "球迷对{subject}分歧太大，短期舆论压力会很高。",
        ],
    },
    "iaa_game": {
        "filename": "iaa_game_comments.csv",
        "platforms": ["weibo", "bili", "tap", "douyin"],
        "topic": "IAA Game Review Pain Point Mining",
        "subjects": ["新手关卡", "激励广告", "失败结算", "体力系统", "抽卡活动", "匹配模式", "剧情副本", "每日任务"],
        "positive": [
            "{subject}节奏挺爽，碎片时间打开玩两把刚好。",
            "{subject}奖励给得还算大方，广告如果自愿看可以接受。",
            "画风比同类IAA游戏舒服，{subject}没有太重的学习成本。",
            "{subject}反馈很即时，连胜的时候确实有继续玩的动力。",
            "剧情和关卡包装比预期好，{subject}不是纯换皮。",
            "{subject}上手简单，适合通勤路上玩。",
        ],
        "neutral": [
            "{subject}可以继续观察，前十分钟体验还行，后面要看广告频率。",
            "我不反对广告变现，但{subject}最好把触发点讲清楚。",
            "{subject}现在属于能玩，但长期留存还要看更新节奏。",
            "建议把{subject}的数据和关卡难度分开展示，不然不好判断。",
            "如果后续活动稳定，{subject}可能会留下来。",
            "{subject}需要更多解释，不然新玩家不知道资源怎么用。",
        ],
        "negative": [
            "{subject}强制广告太多，刚进入关键环节就被打断。",
            "{subject}卡顿和发热明显，手机玩十分钟就烫。",
            "氪金礼包弹窗有点密，{subject}给人的压力很大。",
            "{subject}数值不平衡，连续遇到高战力对手很劝退。",
            "新手引导太长，{subject}一直打断操作节奏。",
            "{subject}奖励广告可以有，但不要每一关都强制看。",
        ],
    },
    "news_event": {
        "filename": "news_event_comments.csv",
        "platforms": ["weibo", "zhihu", "bili", "toutiao"],
        "topic": "News Event Public Opinion Analysis",
        "subjects": ["发布会回应", "调查进展", "媒体报道", "专家解读", "官方通报", "现场视频", "评论区讨论", "后续处理"],
        "positive": [
            "{subject}把时间线讲清楚了，比只看热搜标题靠谱。",
            "支持继续公开信息，{subject}至少回应了大家最关心的问题。",
            "{subject}有事实依据，能减少很多无效争吵。",
            "这次{subject}比较克制，没有把情绪往对立上带。",
            "{subject}补充了背景信息，普通人更容易理解事件。",
            "如果后续也保持透明，{subject}会提升公众信任。",
        ],
        "neutral": [
            "{subject}目前信息还不完整，先等正式结论。",
            "只看{subject}还不能判断全貌，需要更多原始材料。",
            "{subject}有价值，但评论区很多人把立场和事实混在一起。",
            "建议把{subject}里的关键节点做成时间线。",
            "现在争议点主要在信息差，不一定是单纯情绪对立。",
            "{subject}需要持续更新，不然很快会被二次解读带偏。",
        ],
        "negative": [
            "{subject}解释不够透明，关键细节还是没说清楚。",
            "担心{subject}只是在转移重点，没有回应核心质疑。",
            "{subject}里有些表述前后不一致，容易造成信任问题。",
            "评论区围绕{subject}已经明显对立，平台需要降温。",
            "{subject}如果没有证据支撑，就会被当成公关话术。",
            "很多人质疑{subject}的立场，说明信息发布节奏有问题。",
        ],
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate high-signal demo comment datasets.")
    parser.add_argument("--scenario", choices=[*SCENARIOS.keys(), "all"], default="all")
    parser.add_argument("--rows", type=int, default=320, help="Rows per scenario. Must be at least 300 for README demos.")
    args = parser.parse_args()

    if args.rows < 300:
        raise ValueError("--rows must be at least 300")

    generate_demo_data(args.scenario, args.rows)


def generate_demo_data(scenario: str = "all", rows_per_scenario: int = 320) -> None:
    """Generate demo CSV files for one scenario or all scenarios."""

    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    scenarios = SCENARIOS.keys() if scenario == "all" else [scenario]
    for scenario_name in scenarios:
        path = DEMO_DIR / SCENARIOS[scenario_name]["filename"]
        rows = build_rows(scenario_name, rows_per_scenario)
        write_csv(path, rows)
        print(f"Wrote {len(rows)} rows: {path.relative_to(PROJECT_ROOT)}")


def build_rows(scenario: str, count: int) -> list[dict[str, str | int]]:
    config = SCENARIOS[scenario]
    buckets = ["positive", "neutral", "negative"]
    now = datetime(2026, 6, 20, tzinfo=timezone.utc)
    rows: list[dict[str, str | int]] = []
    for index in range(count):
        bucket = buckets[index % len(buckets)]
        template = config[bucket][(index // len(buckets)) % len(config[bucket])]
        subject = config["subjects"][(index * 5 + index // 7) % len(config["subjects"])]
        platform = config["platforms"][(index * 3 + index // 11) % len(config["platforms"])]
        content = enrich_text(template.format(subject=subject), scenario, bucket, index)
        comment_id = f"{scenario}-{index + 1:04d}"
        published_at = now - timedelta(minutes=37 * index)
        rows.append(
            {
                "id": comment_id,
                "platform": platform,
                "topic": config["topic"],
                "content": content,
                "author_hash": hashlib.sha1(f"{scenario}:{platform}:{index}".encode("utf-8")).hexdigest()[:16],
                "like_count": 3 + (index * 17) % 260,
                "reply_count": (index * 7) % 38,
                "publish_time": published_at.isoformat(),
                "source_url": f"https://example.com/demo/{scenario}/{comment_id}",
            }
        )
    return rows


def enrich_text(text: str, scenario: str, bucket: str, index: int) -> str:
    tails = {
        "nba_draft": {
            "positive": ["适合做球员模板拆解。", "球队需求也对得上。", "这类观点适合跟体测数据一起看。"],
            "neutral": ["先标记为信息补充。", "需要和更多比赛样本交叉验证。", "别把单场表现当结论。"],
            "negative": ["这个风险需要单独解释。", "别只用集锦证明上限。", "这会影响选秀夜舆论。"],
        },
        "iaa_game": {
            "positive": ["这个点适合做商店页卖点。", "如果留存数据也好就值得放大。", "可以沉淀成素材标题。"],
            "neutral": ["建议继续观察次留和广告完成率。", "需要拆开新老用户看。", "最好补充更多设备样本。"],
            "negative": ["这是高优先级体验风险。", "建议先做频控实验。", "很容易变成差评关键词。"],
        },
        "news_event": {
            "positive": ["适合做信息澄清卡片。", "这种表达能降低误读。", "可以作为正向传播证据。"],
            "neutral": ["建议继续追踪观点变化。", "先不要过度判断立场。", "需要结合后续通报。"],
            "negative": ["这是舆情风险点。", "需要明确证据来源。", "如果拖延会放大不信任。"],
        },
    }
    tail = tails[scenario][bucket][index % 3]
    nuance = ["", " 我看评论区也有人持相反意见。", " 高赞区已经开始讨论。", " 这个角度比单纯情绪更重要。"][index % 4]
    return f"{text}{nuance}{tail}"


def write_csv(path: Path, rows: list[dict[str, str | int]]) -> None:
    fieldnames = ["id", "platform", "topic", "content", "author_hash", "like_count", "reply_count", "publish_time", "source_url"]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
