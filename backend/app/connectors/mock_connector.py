from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha1

from app.connectors.base import FetchRequest, NormalizedComment


class MockConnector:
    """Mock connector that simulates public comments for hupu, weibo and zhihu."""

    name = "mock"

    _platform_seed = {
        "hupu": [
            "这场比赛最后三分钟太燃了，团队配合真漂亮。",
            "裁判几个判罚真的离谱，情绪都被带起来了。",
            "解说很有激情，但是广告插入太突兀。",
            "选手高光操作值得反复看，剪成短视频肯定能火。",
        ],
        "weibo": [
            "刚玩两分钟就弹广告，真的烦。",
            "画风很舒服，上手也快，适合碎片时间玩。",
            "不是不能看广告，是每一关都让我看。",
            "新版本有点卡顿，手机发热也明显。",
            "奖励广告可以接受，但别强制。",
        ],
        "zhihu": [
            "核心玩法有创意，但数值成长压力偏大。",
            "信息解释不够透明，新手不知道资源该怎么用。",
            "剧情节奏比同类产品更紧凑，这是优势。",
            "匹配机制有点不平衡，连续遇到高战力对手。",
        ],
        "bilibili": [
            "实机画面比宣传片稳，角色动作挺顺。",
            "教程太长，前十分钟一直被打断。",
        ],
        "reddit": [
            "The core loop is fun, but forced ads break the flow.",
            "Matchmaking feels unfair after the latest update.",
        ],
        "youtube": [
            "Great highlight, the comeback was insane.",
            "Too many pre-roll ads before the actual content.",
        ],
    }

    def fetch_comments(self, request: FetchRequest) -> list[NormalizedComment]:
        """Generate deterministic sample comments for the requested platform."""

        base = self._platform_seed.get(request.platform, self._platform_seed["weibo"])
        comments: list[NormalizedComment] = []
        now = datetime.now(timezone.utc)
        target = max(1, min(request.max_comments, len(base)))
        for index, content in enumerate(base[:target], start=1):
            comment_id = f"mock-{request.platform}-{request.task_id}-{index}"
            comments.append(
                {
                    "id": comment_id,
                    "platform": request.platform,
                    "topic": request.semantic_query or ",".join(request.keywords),
                    "content": content,
                    "author_hash": sha1(f"{request.platform}-{index}".encode("utf-8")).hexdigest()[:16],
                    "like_count": 8 + index * 7,
                    "reply_count": index % 4,
                    "publish_time": (now - timedelta(hours=index * 4)).isoformat(),
                    "source_url": f"https://example.com/{request.platform}/{comment_id}",
                    "parent_id": None,
                    "metadata": {"source": "mock", "compliance": "synthetic_public_sample"},
                }
            )
        return comments
