# Sports Taxonomy

The public product exposes exactly two taxonomies.

## Basketball

Positive labels:

- 球星表现
- 团队进攻
- 防守强度
- 战术调整
- 关键球执行
- 替补贡献
- 比赛观赏性

Negative labels:

- 裁判判罚争议
- 球员状态低迷
- 防守漏洞
- 战术失误
- 失误与球权
- 伤病影响
- 教练用人争议

## Football

Positive labels:

- 球员发挥
- 进攻组织
- 防守纪律
- 战术执行
- 门将表现
- 替补调整
- 比赛节奏

Negative labels:

- 判罚争议
- 临门一脚
- 防线失误
- 中场失控
- 体能问题
- 教练调整争议
- 伤病影响

Both sports share stance labels for home-team support, away-team support, rational analysis, referee questioning, humor, information supplements, and unrelated comments.

Add terms conservatively in `backend/app/taxonomies/domain_taxonomy.py` and accompany every new label family with a test. Do not add unrelated product, game, esports, or general-news taxonomies.
