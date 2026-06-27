from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DomainTaxonomy:
    """Domain-specific labels and keyword hints used by rule-based agents."""

    domain: str
    positive_labels: list[str]
    negative_labels: list[str]
    stance_labels: list[str]
    positive_terms: dict[str, list[str]]
    negative_terms: dict[str, list[str]]
    stance_terms: dict[str, list[str]]

    @property
    def domain_terms(self) -> set[str]:
        terms: set[str] = set()
        for label in self.positive_labels + self.negative_labels + self.stance_labels:
            terms.update(_split_label(label))
            terms.add(label)
        for mapping in (self.positive_terms, self.negative_terms, self.stance_terms):
            for label, words in mapping.items():
                terms.add(label)
                terms.update(words)
        return {term for term in terms if term}


NBA_DRAFT_POSITIVE_LABELS = [
    "天赋与身体模板",
    "年龄与成长空间",
    "技术稀缺性",
    "顺位性价比",
    "球队培养环境",
    "适配球队需求",
    "国际球员潜力",
    "媒体话题热度",
]

NBA_DRAFT_NEGATIVE_LABELS = [
    "对抗能力担忧",
    "移动速度担忧",
    "投篮稳定性担忧",
    "防守覆盖范围",
    "伤病风险",
    "发展周期过长",
    "顺位过高争议",
    "模板过度吹捧",
    "样本联赛含金量争议",
    "球迷认知分歧",
]

NBA_DRAFT_STANCE_LABELS = ["看好", "谨慎看好", "质疑", "反对", "调侃", "信息补充", "无关"]


TAXONOMIES: dict[str, DomainTaxonomy] = {
    "nba_draft": DomainTaxonomy(
        domain="nba_draft",
        positive_labels=NBA_DRAFT_POSITIVE_LABELS,
        negative_labels=NBA_DRAFT_NEGATIVE_LABELS,
        stance_labels=NBA_DRAFT_STANCE_LABELS,
        positive_terms={
            "天赋与身体模板": ["天赋", "身体模板", "身体条件", "静态", "臂展", "尺寸", "上限", "运动能力", "五星"],
            "年龄与成长空间": ["年龄", "年轻", "成长", "潜力", "涨球", "培养", "大一", "高中生", "未来"],
            "技术稀缺性": ["技术", "稀缺", "投射", "持球", "控运", "传球", "策应", "护框", "空间属性"],
            "顺位性价比": ["性价比", "顺位", "捡漏", "赚", "不亏", "值", "低顺位", "乐透末"],
            "球队培养环境": ["培养环境", "培养", "教练", "体系", "发展联盟", "耐心", "养成", "球队文化"],
            "适配球队需求": ["适配", "球队需求", "补强", "阵容", "缺锋线", "缺后卫", "搭配", "即战力"],
            "国际球员潜力": ["国际", "海外", "欧洲", "法国", "澳洲", "塞尔维亚", "FIBA", "国际球员"],
            "媒体话题热度": ["热度", "话题", "媒体", "流量", "曝光", "讨论度", "营销", "关注度"],
        },
        negative_terms={
            "对抗能力担忧": ["对抗", "力量", "太瘦", "单薄", "挂肉", "顶不动", "身体对抗", "篮下对抗"],
            "移动速度担忧": ["移动慢", "横移", "脚步慢", "速度慢", "换防", "敏捷", "跟不上"],
            "投篮稳定性担忧": ["投篮", "三分", "罚球", "不稳定", "命中率", "手感", "铁", "投射差"],
            "防守覆盖范围": ["防守", "覆盖范围", "协防", "护框", "漏人", "防不住", "防守范围"],
            "伤病风险": ["伤病", "受伤", "玻璃", "耐久", "膝盖", "脚踝", "健康风险", "养伤"],
            "发展周期过长": ["周期", "太毛坯", "毛坯", "兑现慢", "几年", "等不起", "项目型", "养成时间"],
            "顺位过高争议": ["顺位过高", "高位", "选高了", "不值", "亏", "水货", "乐透", "前十不值"],
            "模板过度吹捧": ["模板", "吹", "吹过了", "碰瓷", "过度吹捧", "上限吹", "贷款"],
            "样本联赛含金量争议": ["联赛", "含金量", "样本", "强度", "低级别", "NCAA", "海外联赛", "比赛少"],
            "球迷认知分歧": ["分歧", "争议", "看不懂", "球迷", "粉丝", "吵", "两极", "认知"],
        },
        stance_terms={
            "看好": ["看好", "稳", "赚", "真香", "期待", "有戏", "可以冲"],
            "谨慎看好": ["谨慎", "再看看", "有潜力", "待观察", "如果", "但是", "不急"],
            "质疑": ["质疑", "不理解", "为什么", "靠谱吗", "存疑", "看不懂"],
            "反对": ["反对", "别选", "不要", "不值", "亏大了", "水货"],
            "调侃": ["哈哈", "笑死", "离谱", "抽象", "节目效果", "整活"],
            "信息补充": ["资料", "数据", "补充", "其实", "身高", "年龄", "顺位", "来自"],
            "无关": [],
        },
    ),
    "sports": DomainTaxonomy(
        domain="sports",
        positive_labels=["球员高光", "球队适配", "比赛氛围", "战术执行", "媒体传播"],
        negative_labels=["判罚争议", "阵容争议", "伤病风险", "表现低迷", "球迷冲突"],
        stance_labels=["支持", "谨慎支持", "质疑", "反对", "调侃", "信息补充", "无关"],
        positive_terms={
            "球员高光": ["高光", "进球", "破门", "助攻", "爆发", "天赋"],
            "球队适配": ["适配", "补强", "阵容", "配合", "体系"],
            "比赛氛围": ["燃", "氛围", "现场", "热血"],
            "战术执行": ["战术", "执行", "防守", "压迫", "配合"],
            "媒体传播": ["话题", "热度", "转发", "剪辑"],
        },
        negative_terms={
            "判罚争议": ["裁判", "判罚", "误判", "黑哨"],
            "阵容争议": ["阵容", "选人", "轮换", "适配差"],
            "伤病风险": ["伤病", "受伤", "健康"],
            "表现低迷": ["低迷", "拉胯", "失误", "不稳"],
            "球迷冲突": ["球迷", "攻击", "吵", "对立"],
        },
        stance_terms={},
    ),
    "esports": DomainTaxonomy(
        domain="esports",
        positive_labels=["选手表现", "团队配合", "高光操作", "战术执行", "赛事热度"],
        negative_labels=["选手状态差", "战术争议", "裁判争议", "转会争议", "粉丝冲突"],
        stance_labels=["支持", "谨慎支持", "质疑", "反对", "调侃", "信息补充", "无关"],
        positive_terms={
            "选手表现": ["选手", "状态", "carry", "发挥"],
            "团队配合": ["团队", "配合", "协同"],
            "高光操作": ["高光", "操作", "单杀", "五杀"],
            "战术执行": ["战术", "执行", "运营"],
            "赛事热度": ["热度", "话题", "直播"],
        },
        negative_terms={
            "选手状态差": ["状态差", "拉胯", "失误"],
            "战术争议": ["战术", "BP", "阵容"],
            "裁判争议": ["裁判", "判罚"],
            "转会争议": ["转会", "合同"],
            "粉丝冲突": ["粉丝", "攻击", "互喷"],
        },
        stance_terms={},
    ),
    "game": DomainTaxonomy(
        domain="game",
        positive_labels=["玩法爽感", "画风表现", "节奏快", "奖励机制", "上手简单", "剧情内容"],
        negative_labels=["广告过多", "氪金压力", "卡顿闪退", "数值不平衡", "匹配机制问题", "新手引导差"],
        stance_labels=["支持", "谨慎支持", "质疑", "反对", "调侃", "信息补充", "无关"],
        positive_terms={
            "玩法爽感": ["爽", "好玩", "核心玩法", "手感"],
            "画风表现": ["画风", "画面", "角色", "美术"],
            "节奏快": ["节奏", "碎片时间", "紧凑"],
            "奖励机制": ["奖励", "福利", "掉落"],
            "上手简单": ["上手", "简单", "教程清楚"],
            "剧情内容": ["剧情", "内容", "关卡"],
        },
        negative_terms={
            "广告过多": ["广告", "强制", "弹窗", "pre-roll", "forced ads"],
            "氪金压力": ["氪金", "付费", "资源", "逼氪"],
            "卡顿闪退": ["卡顿", "闪退", "发热"],
            "数值不平衡": ["数值", "不平衡", "战力"],
            "匹配机制问题": ["匹配", "不公平", "matchmaking"],
            "新手引导差": ["新手", "教程", "引导"],
        },
        stance_terms={},
    ),
    "news": DomainTaxonomy(
        domain="news",
        positive_labels=["信息价值", "观点认同", "情绪共鸣", "社会议题", "公共影响"],
        negative_labels=["信息不透明", "立场争议", "信任问题", "情绪对立", "事实争议"],
        stance_labels=["支持", "谨慎支持", "质疑", "反对", "调侃", "信息补充", "无关"],
        positive_terms={
            "信息价值": ["信息", "解释", "梳理"],
            "观点认同": ["认同", "支持", "有道理"],
            "情绪共鸣": ["共鸣", "感动", "理解"],
            "社会议题": ["社会", "公共", "议题"],
            "公共影响": ["影响", "改变", "关注"],
        },
        negative_terms={
            "信息不透明": ["不透明", "解释不够", "信息缺失"],
            "立场争议": ["立场", "偏向", "争议"],
            "信任问题": ["信任", "造假", "不可信"],
            "情绪对立": ["对立", "吵", "攻击"],
            "事实争议": ["事实", "证据", "不实"],
        },
        stance_terms={},
    ),
}

TAXONOMIES["iaa_game"] = DomainTaxonomy(
    domain="iaa_game",
    positive_labels=["玩法爽感", "广告可接受度", "美术表现", "轻量化体验", "奖励反馈", "内容包装"],
    negative_labels=["强制广告打断", "广告频率过高", "卡顿发热", "付费压力", "数值不平衡", "新手引导过长", "留存风险"],
    stance_labels=["认可", "谨慎认可", "质疑", "反对", "调侃", "信息补充", "无关"],
    positive_terms={
        "玩法爽感": ["爽", "好玩", "手感", "反馈即时", "连胜", "节奏"],
        "广告可接受度": ["激励广告", "自愿看", "可以接受", "奖励广告"],
        "美术表现": ["画风", "画面", "美术", "角色", "包装"],
        "轻量化体验": ["碎片时间", "通勤", "轻量", "上手简单", "学习成本"],
        "奖励反馈": ["奖励", "福利", "大方", "掉落", "反馈"],
        "内容包装": ["剧情", "关卡", "副本", "不是纯换皮", "活动"],
    },
    negative_terms={
        "强制广告打断": ["强制广告", "被打断", "弹广告", "关键环节", "强制看"],
        "广告频率过高": ["广告太多", "广告频率", "每一关", "频控", "广告完成率"],
        "卡顿发热": ["卡顿", "发热", "烫", "闪退", "性能"],
        "付费压力": ["氪金", "礼包", "弹窗", "付费", "压力"],
        "数值不平衡": ["数值不平衡", "高战力", "匹配", "劝退", "难度"],
        "新手引导过长": ["新手引导", "教程", "太长", "打断操作"],
        "留存风险": ["留存", "次留", "卸载", "长期", "更新节奏"],
    },
    stance_terms={
        "认可": ["认可", "舒服", "愿意留下", "可以接受", "挺好"],
        "谨慎认可": ["还行", "继续观察", "后面要看", "如果", "但"],
        "质疑": ["质疑", "不理解", "为什么", "不好判断"],
        "反对": ["别", "不要", "劝退", "卸载"],
        "调侃": ["哈哈", "笑死", "离谱", "抽象"],
        "信息补充": ["数据", "补充", "建议", "最好", "需要"],
        "无关": [],
    },
)


def get_taxonomy(domain: str | None) -> DomainTaxonomy:
    """Return a known taxonomy, falling back to game for legacy demos."""

    return TAXONOMIES.get((domain or "game").strip().lower(), TAXONOMIES["game"])


def classify_label(text: str, domain: str, polarity: str) -> tuple[str, str, float]:
    """Return best label, matched term, and rule confidence."""

    taxonomy = get_taxonomy(domain)
    mapping = taxonomy.positive_terms if polarity == "positive" else taxonomy.negative_terms
    lower = text.lower()
    best_label = ""
    best_term = ""
    best_len = 0
    for label, terms in mapping.items():
        for term in terms:
            term_lower = term.lower()
            if term_lower and term_lower in lower and len(term_lower) > best_len:
                best_label = label
                best_term = term
                best_len = len(term_lower)
    labels = taxonomy.positive_labels if polarity == "positive" else taxonomy.negative_labels
    if best_label:
        return best_label, best_term, 0.82
    return labels[0], "", 0.55


def classify_stance(text: str, domain: str) -> tuple[str, str, float]:
    """Classify a simple discussion stance."""

    taxonomy = get_taxonomy(domain)
    lower = text.lower()
    for label, terms in taxonomy.stance_terms.items():
        for term in terms:
            if term.lower() in lower:
                return label, term, 0.78
    return taxonomy.stance_labels[-1], "", 0.45


def _split_label(label: str) -> set[str]:
    separators = ["与", "和", "及", "、", "/", " "]
    parts = {label}
    for separator in separators:
        parts.update(part for part in label.split(separator) if len(part) > 1)
    return parts
