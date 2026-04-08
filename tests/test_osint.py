import pytest

from strategify.osint.features import (
    analyze_sentiment,
    analyze_texts_sentiment,
    compute_region_features,
)


class TestAnalyzeSentiment:
    def test_returns_dict_with_compound(self):
        result = analyze_sentiment("Some text")
        assert "compound" in result
        assert "neg" in result
        assert "pos" in result
        assert "neu" in result

    def test_negative_text_has_negative_compound(self):
        result = analyze_sentiment("Troops deployed to border, tensions escalate")
        assert result["compound"] < 0

    def test_positive_text_has_positive_compound(self):
        result = analyze_sentiment("Peace agreement reached between nations")
        assert result["compound"] > 0

    def test_neutral_text_near_zero(self):
        result = analyze_sentiment("The meeting was held today")
        assert -0.3 <= result["compound"] <= 0.3


class TestAnalyzeTextsSentiment:
    def test_empty_list(self):
        result = analyze_texts_sentiment([])
        assert result["tension_score"] == 0.0
        assert result["mean_compound"] == 0.0

    def test_single_negative_text(self):
        result = analyze_texts_sentiment(["Hostile forces attack civilian targets, crisis deepens"])
        assert result["tension_score"] > 0.0
        assert result["mean_compound"] < 0.0

    def test_mixed_texts(self):
        texts = [
            "Peace talks progress smoothly",
            "Troops continue to amass near territory",
        ]
        result = analyze_texts_sentiment(texts)
        assert 0.0 <= result["tension_score"] <= 1.0
        assert result["min_compound"] <= result["mean_compound"] <= result["max_compound"]


class TestComputeRegionFeatures:
    def test_without_texts(self):
        from unittest.mock import MagicMock

        wm = MagicMock()
        wm.regions = [{"region_id": "alpha"}, {"region_id": "bravo"}]
        result = compute_region_features(wm)
        assert "alpha" in result
        assert "bravo" in result
        assert "instability_index" in result["alpha"]
        assert result["alpha"]["tension_score"] == 0.0

    def test_with_texts(self):
        from unittest.mock import MagicMock

        wm = MagicMock()
        wm.regions = [{"region_id": "alpha"}]
        region_texts = {
            "alpha": [
                "Military escalation threatens peace",
                "Diplomats negotiate ceasefire",
            ],
        }
        result = compute_region_features(wm, region_texts=region_texts)
        assert "sentiment_compound" in result["alpha"]
        assert "tension_score" in result["alpha"]
        # Mixed sentiment — tension should be low since there's a positive text
        assert result["alpha"]["tension_score"] < 0.5

    def test_high_tension_scenario(self):
        from unittest.mock import MagicMock

        wm = MagicMock()
        wm.regions = [{"region_id": "bravo"}]
        region_texts = {
            "bravo": [
                "War imminent as troops cross border",
                "Civilian casualties reported in conflict zone",
                "Nation declares martial law",
            ],
        }
        result = compute_region_features(wm, region_texts=region_texts)
        assert result["bravo"]["tension_score"] > 0.3

    def test_invalid_world_map_raises(self):
        with pytest.raises(TypeError, match="must have a 'regions' attribute"):
            compute_region_features("not_a_map")
