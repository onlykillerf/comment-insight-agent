from __future__ import annotations

from app.services.data_quality_service import SMALL_SAMPLE_WARNING, DataQualityService
from app.taxonomies import classify_label, get_taxonomy


def test_data_quality_report_counts_are_correct() -> None:
    raw_comments = [{"id": str(index)} for index in range(5)]
    comments = [
        {"id": "1", "language": "zh", "is_duplicate": False},
        {"id": "2", "language": "zh", "is_duplicate": False},
        {"id": "3", "language": "en", "is_duplicate": True},
        {"id": "4", "language": "zh", "is_duplicate": False},
    ]

    report = DataQualityService().build(raw_comments, comments)

    assert report["raw_count"] == 5
    assert report["clean_count"] == 4
    assert report["dedup_count"] == 3
    assert report["duplicate_ratio"] == 0.25
    assert report["noise_ratio"] == 0.2
    assert report["language_distribution"] == {"zh": 3, "en": 1}


def test_small_sample_warning_is_present() -> None:
    report = DataQualityService().build([{"id": "1"}], [{"id": "1", "language": "zh", "is_duplicate": False}])

    assert report["sample_confidence_level"] == "low"
    assert report["warning"] == SMALL_SAMPLE_WARNING


def test_basketball_and_football_taxonomies_are_focused() -> None:
    basketball = get_taxonomy("basketball")
    football = get_taxonomy("football")

    assert set([basketball.domain, football.domain]) == {"basketball", "football"}
    assert "关键球执行" in basketball.positive_labels
    assert "裁判判罚争议" in basketball.negative_labels
    assert "门将表现" in football.positive_labels
    assert "临门一脚" in football.negative_labels
    assert classify_label("最后两分钟裁判连续误判", "basketball", "negative")[0] == "裁判判罚争议"
    assert classify_label("门将两次神扑完成零封", "football", "positive")[0] == "门将表现"
