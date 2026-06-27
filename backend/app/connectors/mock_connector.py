from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha1

from app.connectors.base import FetchRequest, NormalizedComment


class MockConnector:
    """Deterministic Hupu-style basketball and football comments for local demos."""

    name = "mock"

    _sport_seed = {
        "basketball": [
            "末节那个挡拆连续打成，主队战术执行真的漂亮。",
            "最后两分钟裁判这几个哨太有争议了，比赛节奏全被切碎。",
            "核心今天关键球太硬，两个三分直接把比赛收走。",
            "客队输在篮板保护，连续让对手抢到前场板不能接受。",
            "教练暂停后的联防调整有效，第三节一下把分差追回来了。",
            "替补后卫是今晚奇兵，上来之后推进速度明显快了。",
            "主队失误太多，关键回合还在粘球，球权处理有问题。",
            "这场对攻质量很高，双方球星都打出了季后赛强度。",
            "不要只怪最后一球，第二节防守漏人已经埋下隐患。",
            "从数据看客队三分命中率不差，真正差距是二次进攻。",
            "那个挑战为什么失败，回放看着明明是先碰到球。",
            "中锋护框和换防都在线，这场防守价值比得分更大。",
            "伤病还是影响了轮换，主力下半场明显跑不动。",
            "哈哈最后那个边线球战术太抽象了，完全没人接球。",
            "别急着分锅，系列赛还没结束，下一场看调整。",
            "补充一下，主队最后五分钟只出现一次失误。",
        ],
        "football": [
            "主队高位压迫做得很好，开场二十分钟完全压住了对手。",
            "这个点球判罚争议太大，VAR 回看也没有解释清楚。",
            "边路突破和倒三角配合很流畅，进球是战术执行的结果。",
            "客队临门一脚太差，三个好机会只换来一次射正。",
            "门将今天两次神扑救命，不然上半场就失去悬念。",
            "中场下半场完全失控，拿不住球也组织不起反击。",
            "教练换人太晚，体能下降后才换边锋已经来不及了。",
            "防线造越位很统一，这场零封不是运气。",
            "最后十分钟的攻防转换太精彩，世界杯就该有这种强度。",
            "别只看控球率，客队真正有威胁的进攻并不多。",
            "红牌之前比赛很均衡，判罚直接改变了走势。",
            "替补前锋上来就进球，这次换人确实立竿见影。",
            "伤停导致左路一直被针对，阵容不整影响很明显。",
            "哈哈这脚空门都能打飞，节目效果拉满。",
            "理性复盘，输球主要是防线失位，不是单个前锋的问题。",
            "补充数据：主队全场完成了十八次射门和七次射正。",
        ],
    }

    def fetch_comments(self, request: FetchRequest) -> list[NormalizedComment]:
        """Generate a bounded synthetic sample for the selected match."""

        base = self._sport_seed.get(request.domain, self._sport_seed["basketball"])
        now = datetime.now(timezone.utc)
        target = max(1, min(request.max_comments, len(base)))
        title = request.match_name or request.semantic_query or "虎扑赛事讨论"
        rows: list[NormalizedComment] = []
        for index, content in enumerate(base[:target], start=1):
            comment_id = f"mock-hupu-{request.task_id}-{index}"
            rows.append(
                {
                    "id": comment_id,
                    "platform": "hupu",
                    "topic": title,
                    "content": content,
                    "author_hash": sha1(f"hupu-{index}".encode("utf-8")).hexdigest()[:16],
                    "like_count": 8 + index * 7,
                    "reply_count": index % 5,
                    "publish_time": (now - timedelta(minutes=index * 11)).isoformat(),
                    "source_url": f"https://example.com/hupu/{comment_id}",
                    "parent_id": None,
                    "metadata": {
                        "source": "mock",
                        "thread_title": title,
                        "thread_excerpt": "用于离线演示的虎扑风格比赛讨论，不代表真实用户观点。",
                        "board": request.board,
                        "sport": request.domain,
                        "match_name": request.match_name,
                        "home_team": request.home_team,
                        "away_team": request.away_team,
                        "match_stage": request.match_stage,
                        "match_date": request.match_date,
                        "compliance": "synthetic_public_sample",
                    },
                }
            )
        return rows
