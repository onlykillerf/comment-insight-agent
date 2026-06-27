from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DomainTaxonomy:
    """Sport-specific labels and keyword hints used by rule-based agents."""

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
        for label in self.positive_labels + self.negative_labels:
            terms.update(_split_label(label))
            terms.add(label)
        for mapping in (self.positive_terms, self.negative_terms):
            for label, words in mapping.items():
                terms.add(label)
                terms.update(words)
        return {term for term in terms if term}


TAXONOMIES: dict[str, DomainTaxonomy] = {
    "basketball": DomainTaxonomy(
        domain="basketball",
        positive_labels=["球星表现", "团队进攻", "防守强度", "战术调整", "关键球执行", "替补贡献", "比赛观赏性"],
        negative_labels=["裁判判罚争议", "球员状态低迷", "防守漏洞", "战术失误", "失误与球权", "伤病影响", "教练用人争议"],
        stance_labels=["支持主队", "支持客队", "理性分析", "质疑判罚", "调侃", "信息补充", "无关"],
        positive_terms={
            "球星表现": ["爆发", "超神", "高光", "砍下", "统治", "关键先生", "mvp", "手感火热"],
            "团队进攻": ["团队进攻", "转移球", "分享球", "配合", "挡拆", "空切", "助攻", "进攻流畅"],
            "防守强度": ["防守强度", "锁死", "护框", "抢断", "协防", "轮转", "防守到位"],
            "战术调整": ["战术调整", "暂停有效", "变阵", "针对", "错位", "夹击", "联防"],
            "关键球执行": ["关键球", "绝杀", "最后一攻", "收比赛", "关键三分", "大心脏"],
            "替补贡献": ["替补", "板凳", "奇兵", "第二阵容", "轮换贡献"],
            "比赛观赏性": ["精彩", "好看", "刺激", "燃", "对攻", "加时", "比赛质量"],
        },
        negative_terms={
            "裁判判罚争议": ["裁判", "判罚", "误判", "漏判", "黑哨", "体毛哨", "挑战失败"],
            "球员状态低迷": ["低迷", "拉胯", "铁", "隐身", "手感差", "打得差", "梦游"],
            "防守漏洞": ["漏人", "防不住", "篮板丢", "护框差", "防守漏洞", "被一步过"],
            "战术失误": ["战术失败", "没有战术", "暂停不用", "应变慢", "进攻停滞", "乱打"],
            "失误与球权": ["失误", "球权", "粘球", "浪投", "处理球", "控球失误"],
            "伤病影响": ["伤病", "受伤", "带伤", "缺阵", "伤退", "健康"],
            "教练用人争议": ["用人", "轮换", "教练", "不上", "换人", "首发", "时间分配"],
        },
        stance_terms={
            "支持主队": ["主队", "拿下", "必胜", "冲", "我们赢", "主场"],
            "支持客队": ["客队", "客场拿下", "反客为主", "客场赢"],
            "理性分析": ["理性", "从数据看", "战术上", "回看", "关键在", "原因是"],
            "质疑判罚": ["裁判", "判罚", "误判", "黑哨", "哨子"],
            "调侃": ["哈哈", "笑死", "离谱", "抽象", "节目效果", "绷不住"],
            "信息补充": ["数据", "补充", "统计", "回放", "消息", "伤病报告"],
            "无关": [],
        },
    ),
    "football": DomainTaxonomy(
        domain="football",
        positive_labels=["球员发挥", "进攻组织", "防守纪律", "战术执行", "门将表现", "替补调整", "比赛节奏"],
        negative_labels=["判罚争议", "临门一脚", "防线失误", "中场失控", "体能问题", "教练调整争议", "伤病影响"],
        stance_labels=["支持主队", "支持客队", "理性分析", "质疑判罚", "调侃", "信息补充", "无关"],
        positive_terms={
            "球员发挥": ["梅开二度", "帽子戏法", "进球", "助攻", "高光", "世界波", "突破"],
            "进攻组织": ["进攻组织", "传控", "渗透", "边路", "反击", "直塞", "配合"],
            "防守纪律": ["防守纪律", "封堵", "拦截", "盯人", "造越位", "防线稳"],
            "战术执行": ["战术执行", "高位压迫", "低位防守", "阵型", "针对", "跑位"],
            "门将表现": ["门将", "扑救", "神扑", "零封", "出击"],
            "替补调整": ["替补", "换人有效", "奇兵", "替补建功"],
            "比赛节奏": ["节奏", "精彩", "好看", "对攻", "攻防转换", "比赛质量"],
        },
        negative_terms={
            "判罚争议": ["裁判", "判罚", "越位", "点球", "红牌", "黄牌", "var", "误判"],
            "临门一脚": ["临门一脚", "射门", "吐饼", "浪费机会", "打飞", "射正"],
            "防线失误": ["防线", "漏人", "失位", "乌龙", "回传失误", "被打穿"],
            "中场失控": ["中场失控", "拿不住球", "出球困难", "被压制", "中场脱节"],
            "体能问题": ["体能", "跑不动", "抽筋", "疲劳", "下半场崩"],
            "教练调整争议": ["教练", "换人", "阵型", "首发", "调整太晚", "用人"],
            "伤病影响": ["伤病", "受伤", "伤退", "缺阵", "带伤"],
        },
        stance_terms={
            "支持主队": ["主队", "主场", "拿下", "晋级", "我们赢", "必胜"],
            "支持客队": ["客队", "客场", "反客为主", "客场赢", "客队晋级"],
            "理性分析": ["理性", "战术上", "从数据看", "关键在", "原因是", "复盘"],
            "质疑判罚": ["裁判", "判罚", "越位", "点球", "var", "红牌"],
            "调侃": ["哈哈", "笑死", "离谱", "抽象", "节目效果", "整活"],
            "信息补充": ["数据", "补充", "统计", "回放", "首发", "伤病报告"],
            "无关": [],
        },
    ),
}


ALIASES = {
    "sports": "basketball",
    "nba": "basketball",
    "nba_draft": "basketball",
    "soccer": "football",
    "world_cup": "football",
}


def get_taxonomy(domain: str | None) -> DomainTaxonomy:
    """Return one of the two public sports taxonomies."""

    key = (domain or "basketball").strip().lower()
    return TAXONOMIES.get(ALIASES.get(key, key), TAXONOMIES["basketball"])


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
    """Classify a simple match-discussion stance."""

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
