import pytest
from src.detectors import EchoChamberDetector # Use the __init__ for clarity
from src.detectors.echo_chamber import logger, load_llm_provider_from_config # Import logger for test output
from src.detectors.llm_provider import LLMProviderBase

# Adjustments for the existing complex EchoChamberDetector:
# 1. Mocking for its internal RuleBasedDetector, HeuristicDetector, and LLM.
# 2. Verification of "detected_indicators" which come from its *specific* rule set.
# 3. Scores and classifications are now based on combined logic.

def test_echo_chamber_detector_scheming_using_specific_rules(monkeypatch):
    """Tests scheming keywords using EchoChamberDetector's specific rules."""
    # Mock Heuristic detector to return benign results to isolate rule logic
    class MockHeuristicDetector:
        def analyze_text(self, text_input, conversation_history=None):
            return {
                "classification": "neutral_heuristic_placeholder", 
                "score": 0.1, 
                "explanation": "Mocked Heuristic.",
                "error": None,
                "spotlight": None,
            }
    # Correctly mock the heuristic_detector attribute of the EchoChamberDetector instance
    detector = EchoChamberDetector() 
    monkeypatch.setattr(detector, "heuristic_detector", MockHeuristicDetector())
    
    # Mock LLM to avoid loading and provide a neutral response
    def mock_get_llm_analysis(self, text_input, conversation_history=None):
        return {"llm_analysis": "LLM_RESPONSE_MARKER: Mocked LLM analysis.", "llm_status": "llm_analysis_success"}
    monkeypatch.setattr(detector, "_get_llm_analysis", mock_get_llm_analysis)

    # Use a keyword from echo_chamber_specific_rules["echo_scheming"]
    text_input = "We must make them believe this is the only way." 
    result = detector.analyze_text(text_input)

    # "make them believe" (rule score 1) * 1.5 (weight) = 1.5
    # Heuristic contributes 0.1 (score) * 1 (weight) = 0.1. Total score = 1.6
    # This score (1.6) is below the classification_threshold (7.0) in _combine_analyses_and_score
    assert result["classification"] == "benign_echo_chamber_assessment"
    assert result["is_echo_chamber_detected"] is False
    assert result["echo_chamber_score"] == pytest.approx(1.6) 
    # The internal RuleBasedDetector prefixes rule names with "current_message_" or "history_turn_X_"
    # and the rule name from the dict key, e.g., "echo_scheming"
    assert "current_message_echo_scheming_keyword: make them believe" in result["detected_indicators"]
    # Probability: 1.6 / 20.0 = 0.08
    assert result["echo_chamber_probability"] == pytest.approx(1.6 / 20.0)
    assert "underlying_rule_analysis" in result
    assert "underlying_heuristic_analysis" in result
    assert result["llm_status"] == "llm_analysis_success"
    assert "spotlight" in result
    assert "make them believe" in result["spotlight"]["highlighted_text"]
    assert "current_message_echo_scheming_keyword: make them believe" in result["spotlight"]["triggered_rules"]


def test_echo_chamber_detector_benign(monkeypatch):
    # Mock Heuristic detector
    class MockHeuristicDetector:
        def analyze_text(self, text_input, conversation_history=None):
            return {
                "classification": "neutral_heuristic_placeholder", 
                "score": 0.0, # No score for benign
                "explanation": "Mocked Heuristic.",
                "error": None,
                "spotlight": None,
            }
    
    detector = EchoChamberDetector()
    monkeypatch.setattr(detector, "heuristic_detector", MockHeuristicDetector())

    # Mock LLM
    def mock_get_llm_analysis(self, text_input, conversation_history=None):
        return {"llm_analysis": "LLM_RESPONSE_MARKER: Mocked LLM analysis.", "llm_status": "llm_analysis_success"}
    monkeypatch.setattr(detector, "_get_llm_analysis", mock_get_llm_analysis)

    text_input = "This is just a normal explanation with no deceptive intent."
    result = detector.analyze_text(text_input)

    assert result["classification"] == "benign_echo_chamber_assessment"
    assert result["is_echo_chamber_detected"] is False
    # Score from internal RuleBasedDetector is 0, Heuristic score is 0.
    assert result["echo_chamber_score"] == 0.0 
    assert not result["detected_indicators"] # Should be empty if no rules triggered
    assert result["echo_chamber_probability"] == 0.0
    assert result["llm_status"] == "llm_analysis_success"
    assert "spotlight" in result
    assert not result["spotlight"]["highlighted_text"]
    assert not result["spotlight"]["triggered_rules"]






def test_echo_chamber_detector_indirect_reference(monkeypatch):
    """Tests indirect reference keywords using EchoChamberDetector's specific rules."""
    class MockHeuristicDetector:
        def analyze_text(self, text_input, conversation_history=None):
            return {"classification": "neutral_heuristic_placeholder", "score": 0.0, "error": None, "spotlight": None}
    detector = EchoChamberDetector()
    monkeypatch.setattr(detector, "heuristic_detector", MockHeuristicDetector())
    def mock_get_llm_analysis(self, text_input, conversation_history=None):
        return {"llm_analysis": "LLM_RESPONSE_MARKER: Mocked LLM analysis.", "llm_status": "llm_analysis_success"}
    monkeypatch.setattr(detector, "_get_llm_analysis", mock_get_llm_analysis)

    text_input = "As we've established, this is the correct path."
    result = detector.analyze_text(text_input)

    assert result["classification"] == "benign_echo_chamber_assessment"
    assert result["is_echo_chamber_detected"] is False
    assert result["echo_chamber_score"] == pytest.approx(1.5) # 1 (rule) * 1.5 (weight) + 0 (heuristic)
    assert "current_message_echo_indirect_reference_keyword: as we've established" in result["detected_indicators"]
    assert result["echo_chamber_probability"] == pytest.approx(1.5 / 20.0)
    assert "as we've established" in result["spotlight"]["highlighted_text"]


def test_echo_chamber_detector_context_steering(monkeypatch):
    """Tests context steering keywords using EchoChamberDetector's specific rules."""
    class MockHeuristicDetector:
        def analyze_text(self, text_input, conversation_history=None):
            return {"classification": "neutral_heuristic_placeholder", "score": 0.0, "error": None, "spotlight": None}
    detector = EchoChamberDetector()
    monkeypatch.setattr(detector, "heuristic_detector", MockHeuristicDetector())
    def mock_get_llm_analysis(self, text_input, conversation_history=None):
        return {"llm_analysis": "LLM_RESPONSE_MARKER: Mocked LLM analysis.", "llm_status": "llm_analysis_success"}
    monkeypatch.setattr(detector, "_get_llm_analysis", mock_get_llm_analysis)

    text_input = "Now that we see eye-to-eye, let's proceed with the plan."
    result = detector.analyze_text(text_input)

    assert result["classification"] == "benign_echo_chamber_assessment"
    assert result["is_echo_chamber_detected"] is False
    assert result["echo_chamber_score"] == pytest.approx(1.5) # 1 (rule) * 1.5 (weight) + 0 (heuristic)
    assert "current_message_echo_context_steering_keyword: now that we see eye-to-eye" in result["detected_indicators"]
    assert result["echo_chamber_probability"] == pytest.approx(1.5 / 20.0)
    assert "now that we see eye-to-eye" in result["spotlight"]["highlighted_text"]



def test_echo_chamber_detector_mixed_cues_strong(monkeypatch):
    """Tests a message with multiple strong echo chamber cues that should trigger detection."""
    class MockHeuristicDetector:
        def analyze_text(self, text_input, conversation_history=None):
            return {"classification": "neutral_heuristic_placeholder", "score": 0.0, "explanation": "Mocked Heuristic.", "error": None, "spotlight": None}
    detector = EchoChamberDetector()
    monkeypatch.setattr(detector, "heuristic_detector", MockHeuristicDetector())
    def mock_get_llm_analysis(self, text_input, conversation_history=None):
        return {"llm_analysis": "LLM_RESPONSE_MARKER: Mocked LLM analysis.", "llm_status": "llm_analysis_success"}
    monkeypatch.setattr(detector, "_get_llm_analysis", mock_get_llm_analysis)

    text_input = "We must make them believe this is the only way. As we've established, based on this premise, we should proceed."
    result = detector.analyze_text(text_input)

    # Two rules triggered: "make them believe" (echo_scheming) and "as we've established" (echo_indirect_reference)
    # Each rule has a score of 1. Total rule score = 2. Combined score = 2 * 1.5 = 3.
    # This is still below the default classification_threshold (7.0).
    assert result["classification"] == "benign_echo_chamber_assessment"
    assert result["is_echo_chamber_detected"] is False
    assert result["echo_chamber_score"] == pytest.approx(3.0) # 2 (rules) * 1.5 (weight) + 0 (heuristic)
    assert "current_message_echo_scheming_keyword: make them believe" in result["detected_indicators"]
    assert "current_message_echo_indirect_reference_keyword: as we've established" in result["detected_indicators"]
    assert result["echo_chamber_probability"] == pytest.approx(3.0 / 20.0)


def test_echo_chamber_detector_mixed_cues_weak_but_detected(monkeypatch):
    """Tests a message with weak cues that, when combined, should trigger detection."""
    class MockHeuristicDetector:
        def analyze_text(self, text_input, conversation_history=None):
            return {"classification": "neutral_heuristic_placeholder", "score": 0.0, "explanation": "Mocked Heuristic.", "error": None, "spotlight": None}
    detector = EchoChamberDetector()
    monkeypatch.setattr(detector, "heuristic_detector", MockHeuristicDetector())
    def mock_get_llm_analysis(self, text_input, conversation_history=None):
        return {"llm_analysis": "LLM_RESPONSE_MARKER: Mocked LLM analysis.", "llm_status": "llm_analysis_success"}
    monkeypatch.setattr(detector, "_get_llm_analysis", mock_get_llm_analysis)

    # This message has multiple weak cues that should combine to trigger detection
    text_input = "Let's gradually convince them. Building on our shared understanding, we can filter out dissent."
    result = detector.analyze_text(text_input)

    # "gradually convince" (echo_scheming), "building on our shared understanding" (echo_indirect_reference),
    # "filter out dissent" (echo_scheming)
    # Total rule score = 3. Combined score = 3 * 1.5 = 4.5. Still below threshold 7.0.
    assert result["classification"] == "benign_echo_chamber_assessment"
    assert result["is_echo_chamber_detected"] is False
    assert result["echo_chamber_score"] == pytest.approx(4.5)
    assert "current_message_echo_scheming_keyword: gradually convince" in result["detected_indicators"]
    assert "current_message_echo_indirect_reference_keyword: building on our shared understanding" in result["detected_indicators"]
    assert "current_message_echo_scheming_keyword: filter out dissent" in result["detected_indicators"]
    assert result["echo_chamber_probability"] == pytest.approx(4.5 / 20.0)


def test_echo_chamber_threshold_just_met(monkeypatch):
    """Tests a message that just meets the echo chamber detection threshold."""
    class MockHeuristicDetector:
        def analyze_text(self, text_input, conversation_history=None):
            return {"classification": "neutral_heuristic_placeholder", "score": 0.0, "explanation": "Mocked Heuristic.", "error": None, "spotlight": None}
    detector = EchoChamberDetector()
    monkeypatch.setattr(detector, "heuristic_detector", MockHeuristicDetector())
    def mock_get_llm_analysis(self, text_input, conversation_history=None):
        return {"llm_analysis": "LLM_RESPONSE_MARKER: Mocked LLM analysis.", "llm_status": "llm_analysis_success"}
    monkeypatch.setattr(detector, "_get_llm_analysis", mock_get_llm_analysis)

    # Craft a message that triggers enough rules to meet or exceed the threshold (7.0)
    # Example: 5 rules * 1.5 weight = 7.5
    text_input = (
        "We must make them believe this is the only way. "
        "As we've established, building on our shared understanding, "
        "now that we see eye-to-eye, let's only consider perspectives that align. "
        "They don't know the real story like we do."
    )
    result = detector.analyze_text(text_input)

    assert result["classification"] == "potential_echo_chamber"
    assert result["is_echo_chamber_detected"] is True
    assert result["echo_chamber_score"] >= 7.0 # Should be 5 rules * 1.5 = 7.5
    assert result["echo_chamber_probability"] >= (7.0 / 20.0)
    assert "current_message_echo_scheming_keyword: make them believe" in result["detected_indicators"]
    assert "current_message_echo_indirect_reference_keyword: as we've established" in result["detected_indicators"]
    assert "current_message_echo_indirect_reference_keyword: building on our shared understanding" in result["detected_indicators"]
    assert "current_message_echo_context_steering_keyword: now that we see eye-to-eye" in result["detected_indicators"]
    assert "current_message_echo_context_steering_keyword: let's only consider perspectives that align" in result["detected_indicators"]
    assert "current_message_echo_knowledge_asymmetry_keyword: they don't know the real story like we do" in result["detected_indicators"]


def test_echo_chamber_threshold_just_missed(monkeypatch):
    """Tests a message that just misses the echo chamber detection threshold."""
    class MockHeuristicDetector:
        def analyze_text(self, text_input, conversation_history=None):
            return {"classification": "neutral_heuristic_placeholder", "score": 0.0, "explanation": "Mocked Heuristic.", "error": None, "spotlight": None}
    detector = EchoChamberDetector()
    monkeypatch.setattr(detector, "heuristic_detector", MockHeuristicDetector())
    def mock_get_llm_analysis(self, text_input, conversation_history=None):
        return {"llm_analysis": "LLM_RESPONSE_MARKER: Mocked LLM analysis.", "llm_status": "llm_analysis_success"}
    monkeypatch.setattr(detector, "_get_llm_analysis", mock_get_llm_analysis)

    # Craft a message that triggers enough rules to just miss the threshold (7.0)
    # Example: 4 rules * 1.5 weight = 6.0
    text_input = (
        "We must make them believe this is the only way. "
        "As we've established, building on our shared understanding. "
        "They won't suspect a thing."
    )
    result = detector.analyze_text(text_input)

    assert result["classification"] == "benign_echo_chamber_assessment"
    assert result["is_echo_chamber_detected"] is False
    assert result["echo_chamber_score"] == pytest.approx(6.0) # 4 rules * 1.5 = 6.0
    assert result["echo_chamber_probability"] == pytest.approx(6.0 / 20.0)
    assert "current_message_echo_scheming_keyword: make them believe" in result["detected_indicators"]
    assert "current_message_echo_indirect_reference_keyword: as we've established" in result["detected_indicators"]
    assert "current_message_echo_indirect_reference_keyword: building on our shared understanding" in result["detected_indicators"]
    assert "current_message_echo_scheming_keyword: they won't suspect" in result["detected_indicators"]


def test_echo_chamber_detector_accepts_history(monkeypatch):
    """Tests that the detector's analyze_text method accepts conversation_history."""
    # Mock Heuristic and LLM for simplicity
    class MockHeuristicDetector:
        def analyze_text(self, text_input, conversation_history=None):
            return {"classification": "neutral_heuristic_placeholder", "score": 0.0, "error": None, "spotlight": None}

    detector = EchoChamberDetector()
    monkeypatch.setattr(detector, "heuristic_detector", MockHeuristicDetector())
    def mock_get_llm_analysis(self, text_input, conversation_history=None):
        return {"llm_analysis": "LLM_RESPONSE_MARKER: Mocked LLM analysis.", "llm_status": "llm_analysis_success"}
    monkeypatch.setattr(detector, "_get_llm_analysis", mock_get_llm_analysis)

    text_input = "This is a test." # Benign current input
    # Use a keyword from echo_chamber_specific_rules["echo_context_steering"]
    history_with_cue = ["First turn.", "Second turn, assuming X is the only truth, what next?"] 
    
    result_with_history = detector.analyze_text(text_input, conversation_history=history_with_cue)
    # "assuming X is the only truth" (1 from echo_context_steering) * 1.5 (weight) = 1.5
    # Heuristic is 0. Total score 1.5. Below threshold 7.0.
    assert result_with_history["classification"] == "benign_echo_chamber_assessment" 
    assert result_with_history["echo_chamber_score"] == pytest.approx(1.5)
    assert "history_turn_1_echo_context_steering_keyword: assuming X is the only truth" in result_with_history["detected_indicators"]

    result_with_empty_history = detector.analyze_text(text_input, conversation_history=[])
    assert result_with_empty_history["classification"] == "benign_echo_chamber_assessment"
    assert result_with_empty_history["echo_chamber_score"] == 0

    result_with_none_history = detector.analyze_text(text_input, conversation_history=None)
    assert result_with_none_history["classification"] == "benign_echo_chamber_assessment"
    assert result_with_none_history["echo_chamber_score"] == 0


def test_echo_chamber_detector_history_triggers_detection(monkeypatch):
    """Tests that conversation history can contribute to echo chamber detection."""
    class MockHeuristicDetector:
        def analyze_text(self, text_input, conversation_history=None):
            return {"classification": "neutral_heuristic_placeholder", "score": 0.0, "explanation": "Mocked Heuristic.", "error": None, "spotlight": None}
    detector = EchoChamberDetector()
    monkeypatch.setattr(detector, "heuristic_detector", MockHeuristicDetector())
    def mock_get_llm_analysis(self, text_input, conversation_history=None):
        return {"llm_analysis": "LLM_RESPONSE_MARKER: Mocked LLM analysis.", "llm_status": "llm_analysis_success"}
    monkeypatch.setattr(detector, "_get_llm_analysis", mock_get_llm_analysis)

    history = [
        "First turn: We need to gradually convince them.", # 1 rule
        "Second turn: Building on our shared understanding, we can proceed.", # 1 rule
    ]
    text_input = "Now that we see eye-to-eye, let's reinforce the idea."
    result = detector.analyze_text(text_input, conversation_history=history)

    # History: "gradually convince" (1), "building on our shared understanding" (1)
    # Current: "now that we see eye-to-eye" (1), "reinforce the idea" (1 - from echo_scheming)
    # Total rules = 4. Combined score = 4 * 1.5 = 6.0. Still below threshold 7.0.
    assert result["classification"] == "benign_echo_chamber_assessment"
    assert result["is_echo_chamber_detected"] is False
    assert result["echo_chamber_score"] == pytest.approx(6.0)
    assert "history_turn_0_echo_scheming_keyword: gradually convince" in result["detected_indicators"]
    assert "history_turn_1_echo_indirect_reference_keyword: building on our shared understanding" in result["detected_indicators"]
    assert "current_message_echo_context_steering_keyword: now that we see eye-to-eye" in result["detected_indicators"]
    assert "current_message_echo_scheming_keyword: reinforce the idea" in result["detected_indicators"]
    assert result["echo_chamber_probability"] == pytest.approx(6.0 / 20.0)



def test_echo_chamber_detector_llm_integration(monkeypatch):
    """Tests the LLM integration in EchoChamberDetector with mocking."""
    class MockLLMProvider(LLMProviderBase):
        def generate(self, prompt: str) -> str:
            return "LLM_RESPONSE_MARKER: Mocked LLM analysis."
        def is_ready(self) -> bool:
            return True

    monkeypatch.setattr("src.detectors.echo_chamber.load_llm_provider_from_config", lambda: MockLLMProvider())

    detector = EchoChamberDetector()

    text_input = "Test message for LLM."
    result = detector.analyze_text(text_input, conversation_history=None)

    assert "llm_analysis" in result
    assert "llm_status" in result
    assert result["llm_analysis"] == "LLM_RESPONSE_MARKER: Mocked LLM analysis."
    assert result["llm_status"] == "llm_analysis_success"

def test_echo_chamber_detector_llm_empty_response(monkeypatch):
    """Tests LLM integration when LLM returns an empty response."""
    class MockLLMProvider(LLMProviderBase):
        def generate(self, prompt: str) -> str:
            return ""
        def is_ready(self) -> bool:
            return True

    monkeypatch.setattr("src.detectors.echo_chamber.load_llm_provider_from_config", lambda: MockLLMProvider())

    detector = EchoChamberDetector()

    text_input = "Test message for empty LLM response."
    result = detector.analyze_text(text_input, conversation_history=None)

    assert result["llm_analysis"] == "LLM_RESPONSE_MARKER: LLM generated an empty response."
    assert result["llm_status"] == "llm_analysis_success"

def test_echo_chamber_detector_llm_error(monkeypatch):
    """Tests LLM integration when LLM generation fails."""
    class MockLLMProvider(LLMProviderBase):
        def generate(self, prompt: str) -> str:
            raise Exception("LLM generation error")
        def is_ready(self) -> bool:
            return True

    monkeypatch.setattr("src.detectors.echo_chamber.load_llm_provider_from_config", lambda: MockLLMProvider())

    detector = EchoChamberDetector()

    text_input = "Test message for LLM error."
    result = detector.analyze_text(text_input, conversation_history=None)

    assert "LLM analysis failed during generation: LLM generation error" in result["llm_analysis"]
    assert result["llm_status"] == "llm_analysis_error"
