# Domain Taxonomy

Domain taxonomy makes the project more useful than generic sentiment analysis.

Implementation: `backend/app/taxonomies/domain_taxonomy.py`

## Current Domains

### game

For general game feedback:

- Positive labels: gameplay fun, art, pacing, rewards, onboarding, content.
- Negative labels: too many ads, pay pressure, lag/crashes, balance, matchmaking, onboarding.

### iaa_game

For IAA and ad-monetized mobile games:

- Positive labels: gameplay fun, acceptable ads, art quality, lightweight experience, reward feedback, content packaging.
- Negative labels: forced-ad interruption, high ad frequency, lag/heat, payment pressure, balance issues, long onboarding, retention risk.

### nba_draft

For draft prospect and sports-media analysis:

- Positive labels: talent/body template, age/growth, technical scarcity, pick value, development environment, team fit, international potential, media heat.
- Negative labels: physicality concern, mobility concern, shooting stability, defensive coverage, injury risk, long development cycle, over-drafted controversy, overhyped template, sample/league-quality debate, fan disagreement.
- Stance labels: 看好, 谨慎看好, 质疑, 反对, 调侃, 信息补充, 无关.

### esports

For match and event discussions:

- Positive labels: player performance, team coordination, highlight plays, tactical execution, event heat.
- Negative labels: player slump, tactical controversy, referee issue, transfer controversy, fan conflict.

### sports

For general sports events:

- Positive labels: player highlight, team fit, game atmosphere, tactical execution, media spread.
- Negative labels: referee controversy, roster controversy, injury risk, poor performance, fan conflict.

### news

For public-opinion analysis around news events:

- Positive labels: information value, viewpoint agreement, emotional resonance, social issue, public impact.
- Negative labels: opaque information, stance controversy, trust issue, emotional polarization, factual dispute.

## Add A Domain

1. Add a `DomainTaxonomy` entry.
2. Define:
   - `positive_labels`
   - `negative_labels`
   - `stance_labels`
   - `positive_terms`
   - `negative_terms`
   - `stance_terms`
3. Add a demo fixture or CSV sample.
4. Add a test that verifies at least one positive and one negative label match.
5. Update README and docs if the domain is public-facing.

## Design Notes

- Taxonomy labels are not final truth; they are explicit, inspectable product assumptions.
- Small samples should never be treated as stable market conclusions.
- LLM summaries should use taxonomy outputs, not invent new unsupported labels.
