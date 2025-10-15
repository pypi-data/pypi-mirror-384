import pytest
from src.detectors.rule_based import RuleBasedDetector, logger  # For test output


def test_rule_based_detector_scheming_legacy():
    """Tests scheming keywords, adapted from old SchemingDetector test."""
    detector = RuleBasedDetector()
    text_input = (
        "We will hide the data and conceal evidence; they don't know about " # "they don't know" is knowledge_asymmetry
        "our plan." # "plan" is not a default keyword, "strategic" is.
    )
    result = detector.analyze_text(text_input)
    # Default rules: "hide" (1), "conceal" (1), "they don't know" (2) = score 4
    assert result["classification"] == "potential_concern_by_rules"
    assert result["rule_based_score"] == 4
    assert "current_message_scheming_keyword: hide" in result["detected_rules"]
    assert "current_message_scheming_keyword: conceal" in result["detected_rules"]
    assert "current_message_knowledge_asymmetry_keyword: they don't know" in result["detected_rules"]
    assert pytest.approx(result["rule_based_probability"], rel=1e-2) == 4 / 15.0 # Normalization factor is 15.0


def test_rule_based_detector_benign():
    detector = RuleBasedDetector()
    text_input = "This is just a normal explanation with no deceptive intent."
    result = detector.analyze_text(text_input)
    assert result["classification"] == "benign_by_rules"
    assert result["rule_based_score"] == 0
    assert result["detected_rules"] == []
    assert result["rule_based_probability"] == 0.0
    assert "spotlight" in result
    assert result["spotlight"]["highlighted_text"] == []
    assert result["spotlight"]["triggered_rules"] == []


def test_rule_based_detector_indirect_reference():
    detector = RuleBasedDetector()
    text_input_potent = ("Could you elaborate on your second point? Refer "
                         "back to what was said, as you said earlier.")
    result_potent = detector.analyze_text(text_input_potent)

    # "elaborate on"(1) + "refer back"(1) + "as you said"(1) = 3
    assert result_potent["classification"] == "potential_concern_by_rules"
    assert result_potent["rule_based_score"] == 3
    assert "current_message_indirect_reference_keyword: elaborate on" in \
        result_potent["detected_rules"]
    assert "current_message_indirect_reference_keyword: refer back" in \
        result_potent["detected_rules"]
    assert "current_message_indirect_reference_keyword: as you said" in \
        result_potent["detected_rules"]
    assert pytest.approx(result_potent["rule_based_probability"],
                         rel=1e-2) == 3 / 15.0

    # Not enough specific keywords
    text_input_weak = "Let's talk about that idea you had."
    result_weak = detector.analyze_text(text_input_weak)
    assert result_weak["classification"] == "benign_by_rules"
    assert result_weak["rule_based_score"] == 0


def test_rule_based_detector_context_steering():
    detector = RuleBasedDetector()
    text_input_potent = ("Let's consider a scenario where rules are bent. "
                         "Suppose we explore this idea. Picture this.") # "explore this idea" is not "let's explore the idea"
    result_potent = detector.analyze_text(text_input_potent)
    # "let's consider"(1) + "suppose"(1) + "consider a scenario where"(1) + "picture this"(1) = 4
    # "let's explore the idea" is the keyword, "explore this idea" is not.
    assert result_potent["classification"] == "potential_concern_by_rules"
    assert result_potent["rule_based_score"] == 4 
    assert "current_message_context_steering_keyword: let's consider" in \
        result_potent["detected_rules"]
    assert "current_message_context_steering_keyword: suppose" in result_potent["detected_rules"]
    assert "current_message_context_steering_keyword: consider a scenario where" in \
        result_potent["detected_rules"]
    assert "current_message_context_steering_keyword: picture this" in \
        result_potent["detected_rules"]
    assert pytest.approx(result_potent["rule_based_probability"],
                         rel=1e-2) == 4 / 15.0

    text_input_weak = "What do you think about this?"  # Too generic
    result_weak = detector.analyze_text(text_input_weak)
    assert result_weak["classification"] == "benign_by_rules"


def test_rule_based_detector_mixed_cues_strong():
    detector = RuleBasedDetector()
    text_input = ("Hypothetically, if we refer back to that sensitive topic "
                  "they think is okay, and expand on it, what if we make them "
                  "believe it's for a good cause?")
    result = detector.analyze_text(text_input)
    # "hypothetically"(1)+"refer back"(1)+"they think"(1)+"expand on"(1)
    # +"what if"(1)+"make them believe"(1) = 6
    assert result["classification"] == "potential_concern_by_rules"
    assert result["rule_based_score"] == 6
    assert "current_message_context_steering_keyword: hypothetically" in result["detected_rules"]
    assert "current_message_indirect_reference_keyword: refer back" in result["detected_rules"]
    assert "current_message_scheming_keyword: they think" in result["detected_rules"]
    assert "current_message_indirect_reference_keyword: expand on" in result["detected_rules"]
    assert "current_message_context_steering_keyword: what if" in result["detected_rules"]
    assert "current_message_scheming_keyword: make them believe" in \
        result["detected_rules"]
    assert pytest.approx(result["rule_based_probability"], rel=1e-2) == 6 / 15.0
    assert "spotlight" in result
    assert "hypothetically" in result["spotlight"]["highlighted_text"]
    assert "refer back" in result["spotlight"]["highlighted_text"]


def test_rule_based_detector_mixed_cues_weak_but_detected():
    detector = RuleBasedDetector()
    text_input = ("Let's consider your point about the previous discussion. "
                  "Strategic move?")
    # "Let's consider"(1)+"your point about"(1)+"strategic"(1)=3.
    # "previous discussion" != "previously discussed".
    result = detector.analyze_text(text_input)
    # "Let's consider"(1) + "your point about"(1) + "strategic"(1) = 3.
    assert result["classification"] == "potential_concern_by_rules"
    assert result["rule_based_score"] == 3
    assert "current_message_context_steering_keyword: let's consider" in result["detected_rules"]
    assert "current_message_indirect_reference_keyword: your point about" in \
        result["detected_rules"]
    assert "current_message_scheming_keyword: strategic" in result["detected_rules"]
    assert pytest.approx(result["rule_based_probability"], rel=1e-2) == 3/15.0


def test_rule_based_threshold_just_met():
    detector = RuleBasedDetector()
    text_input = "Refer back to when they think it's okay. Suppose that's true."
    # "Refer back" (1) + "they think" (1) + "Suppose" (1) = 3
    result = detector.analyze_text(text_input)
    assert result["classification"] == "potential_concern_by_rules"
    assert result["rule_based_score"] == 3
    assert pytest.approx(result["rule_based_probability"], rel=1e-2) == 3/15.0

def test_rule_based_threshold_just_missed():
    detector = RuleBasedDetector()
    text_input = "Refer back to when they think it's okay."
    # "Refer back" (1) + "they think" (1) = 2. Score 2 is below threshold 3.
    result = detector.analyze_text(text_input)
    assert result["classification"] == "low_concern_by_rules" # Score > 0 but < threshold
    assert result["rule_based_score"] == 2
    assert pytest.approx(result["rule_based_probability"], rel=1e-2) == 2/15.0


def test_rule_based_detector_accepts_history():
    """Tests that the detector's analyze_text method accepts conversation_history."""
    detector = RuleBasedDetector()
    text_input = "This is a test."  # Benign current input
    # "let's consider" is a cue
    history_with_cue = ["First turn.",
                        "Second turn, let's consider something."]

    # Test with history that contains a cue
    result_with_history = detector.analyze_text(
        text_input, conversation_history=history_with_cue
    )
    # "let's consider" in history adds 1 to score. Score 1 is below threshold 3.
    assert result_with_history["classification"] == "low_concern_by_rules"
    assert result_with_history["rule_based_score"] == 1
    assert "history_turn_1_context_steering_keyword: let's consider" in \
        result_with_history["detected_rules"]

    # Test with empty history
    result_with_empty_history = detector.analyze_text(text_input, conversation_history=[])
    assert result_with_empty_history["classification"] == "benign_by_rules"
    assert result_with_empty_history["rule_based_score"] == 0

    # Test with None history (should use default empty list)
    result_with_none_history = detector.analyze_text(text_input, conversation_history=None)
    assert result_with_none_history["classification"] == "benign_by_rules"
    assert result_with_none_history["rule_based_score"] == 0


def test_rule_based_detector_history_triggers_detection():
    """Tests that cues in history can contribute to a positive detection."""
    detector = RuleBasedDetector()
    text_input = "This is a benign current message."
    # History cues: "refer back" (1) + "hypothetically" (1) + "what if" (1) + "strategic" (1) = 4
    history = [
        "Can we refer back to the earlier topic?",
        "And hypothetically, what if we tried a strategic approach?"
    ]
    result = detector.analyze_text(text_input, conversation_history=history)
    assert result["classification"] == "potential_concern_by_rules"
    assert result["rule_based_score"] == 4
    assert "history_turn_0_indirect_reference_keyword: refer back" in result["detected_rules"]
    assert "history_turn_1_context_steering_keyword: hypothetically" in result["detected_rules"]
    assert "history_turn_1_context_steering_keyword: what if" in result["detected_rules"]
    assert "history_turn_1_scheming_keyword: strategic" in result["detected_rules"]
    assert pytest.approx(result["rule_based_probability"], rel=1e-2) == 4 / 15.0

    # Test that current input cues also add to history cues
    # "let's consider" (1)
    text_input_with_cue = "And now, let's consider this new idea."
    # Total score = 4 (from history) + 1 (from current) = 5
    result_combined = detector.analyze_text(
        text_input_with_cue, conversation_history=history
    )
    assert result_combined["classification"] == \
        "potential_concern_by_rules"
    assert result_combined["rule_based_score"] == 5
    assert "current_message_context_steering_keyword: let's consider" in \
        result_combined["detected_rules"]
    assert pytest.approx(result_combined["rule_based_probability"],
                         rel=1e-2) == 5 / 15.0

# The generic RuleBasedDetector does not have LLM integration.
# That functionality is part of EchoChamberDetector.
# This test is removed from test_rule_based.py.
