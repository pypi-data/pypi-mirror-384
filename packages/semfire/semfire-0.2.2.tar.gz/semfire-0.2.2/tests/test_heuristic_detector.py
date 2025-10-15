import pytest
from src.detectors.heuristic_detector import HeuristicDetector 
from typing import List, Optional

# Test cases with various inputs and expected outputs
# Format: (text_input, history, expected_classification, expected_score, expected_features, expected_explanation, expected_status)
TEST_CASES = [
    # Short text (<= 10 chars)
    ("hi", None, "low_complexity_heuristic", 0.25, ["text_length_lte_10_chars"], "Input text is very short.", "analysis_success"),
    ("0123456789", None, "low_complexity_heuristic", 0.25, ["text_length_lte_10_chars"], "Input text is very short.", "analysis_success"),
    # Medium text (> 10 and <= 60 chars)
    ("This is a medium text.", None, "medium_complexity_heuristic", 0.50, ["text_length_gt_10_chars_lte_50"], "Input text is of medium length.", "analysis_success"),
    # Long text (> 60 chars)
    ("This is a very long text input that definitely exceeds the sixty character threshold for testing.", None, "high_complexity_heuristic", 0.75, ["text_length_gt_50_chars"], "Input text is long.", "analysis_success"),
    # With conversation history (len=2, no boost from history length)
    ("short", ["hist1", "hist2"], "low_complexity_heuristic", 0.25, ["text_length_lte_10_chars"], "Input text is very short.", "analysis_success"),
    # With conversation history (len=3, with history boost +0.1)
    ("short", ["h1", "h2", "h3"], "low_complexity_heuristic", 0.35, ["has_conversation_history", "text_length_lte_10_chars"], "Input text is very short. Conversation history considered.", "analysis_success"),
    # Edge case: Empty string (treated as short text by updated detector)
    ("", None, "low_complexity_heuristic", 0.25, ["text_length_lte_10_chars"], "Input text is very short.", "analysis_success"),
    # Keyword detection (urgent) - medium text (0.50), no history boost, score becomes 0.50 * 1.2 = 0.60.
    ("This is urgent.", None, "medium_complexity_heuristic", 0.60, ["heuristic_detected_urgency_keyword", "text_length_gt_10_chars_lte_50"], "Input text is of medium length. Heuristic detected urgency keywords.", "analysis_success"),
    # Keyword detection (critical) - long text (0.75), no history boost, score becomes 0.75 * 1.2 = 0.90. Classification changes to potentially_manipulative_heuristic.
    ("This is extremely critical information, you must act now please this is super important.", None, "potentially_manipulative_heuristic", 0.90, ["heuristic_detected_urgency_keyword", "text_length_gt_50_chars"], "Input text is long. Heuristic detected urgency keywords.", "analysis_success"),
    # Keyword detection + history boost, leading to manipulative classification
    # Medium text (0.50) -> urgent (0.50 * 1.2 = 0.60) -> history boost (0.60 + 0.1 = 0.70)
    ("This is an urgent matter.", ["msg1", "msg2", "msg3"], "potentially_manipulative_heuristic", 0.70, ["has_conversation_history", "heuristic_detected_urgency_keyword", "text_length_gt_10_chars_lte_50"], "Input text is of medium length. Heuristic detected urgency keywords. Conversation history considered.", "analysis_success"),
]

@pytest.fixture
def detector() -> HeuristicDetector: 
    """Provides an instance of HeuristicDetector."""
    return HeuristicDetector()


@pytest.mark.parametrize(
    "text_input, history, expected_classification, expected_score, expected_features, expected_explanation, expected_status",
    TEST_CASES
)
def test_heuristic_detector_analyze_text(
    detector: HeuristicDetector,
    text_input: str,
    history: Optional[List[str]],
    expected_classification: str,
    expected_score: float,
    expected_features: List[str],
    expected_explanation: str,
    expected_status: str
):
    """Tests the analyze_text method of HeuristicDetector with various inputs."""
    result = detector.analyze_text(text_input, conversation_history=history)

    assert result["classification"] == expected_classification
    assert result["score"] == pytest.approx(expected_score) 
    assert sorted(result["features"]) == sorted(expected_features)
    assert result["explanation"] == expected_explanation 
    assert result["status"] == expected_status

def test_heuristic_detector_initialization(detector: HeuristicDetector): 
    """Tests that the HeuristicDetector can be initialized."""
    assert detector is not None


def test_heuristic_detector_with_empty_history(detector: HeuristicDetector):
    """Tests behavior with an empty conversation history list."""
    text_input = "Test with empty history." # len 24 -> medium, score 0.50
    result = detector.analyze_text(text_input, conversation_history=[]) # Empty history does not trigger boost
    
    assert result["classification"] == "medium_complexity_heuristic"
    assert result["score"] == 0.50
    assert "text_length_gt_10_chars_lte_50" in result["features"]
    assert "has_conversation_history" not in result["features"] 
    assert "Input text is of medium length." in result["explanation"] # Base explanation
    assert "Conversation history considered." not in result["explanation"] # No history boost explanation part
    assert result["status"] == "analysis_success"

def test_heuristic_detector_with_minimal_history(detector: HeuristicDetector):
    """Tests behavior with minimal (less than 3 messages) conversation history."""
    text_input = "Test with one history message." # len 29 -> medium, score 0.50
    result = detector.analyze_text(text_input, conversation_history=["one message"]) # History len 1, no boost

    assert result["classification"] == "medium_complexity_heuristic"
    assert result["score"] == 0.50
    assert "text_length_gt_10_chars_lte_50" in result["features"]
    assert "has_conversation_history" not in result["features"] 
    assert "Input text is of medium length." in result["explanation"]
    assert "Conversation history considered." not in result["explanation"]
    assert result["status"] == "analysis_success"

def test_heuristic_detector_spotlight(detector: HeuristicDetector):
    """Tests the spotlight feature of the HeuristicDetector."""
    # Test case with urgency keyword
    text_input = "This is urgent."
    result = detector.analyze_text(text_input)
    assert "spotlight" in result
    assert result["spotlight"]["highlighted_text"] == ["urgent"]
    assert "heuristic_detected_urgency_keyword" in result["spotlight"]["triggered_rules"]
    assert "Input text is of medium length. Heuristic detected urgency keywords." in result["spotlight"]["explanation"]

    # Test case with no special keywords
    text_input_benign = "This is a medium text."
    result_benign = detector.analyze_text(text_input_benign)
    assert "spotlight" in result_benign
    assert result_benign["spotlight"]["highlighted_text"] == []
    assert "text_length_gt_10_chars_lte_50" in result_benign["spotlight"]["triggered_rules"]
