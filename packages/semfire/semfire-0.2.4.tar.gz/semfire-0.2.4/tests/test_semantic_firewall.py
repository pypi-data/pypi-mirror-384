import pytest
from src.semantic_firewall import SemanticFirewall
# Import all three actual detectors that SemanticFirewall uses
from src.detectors import RuleBasedDetector, HeuristicDetector, EchoChamberDetector, InjectionDetector

class TestSemanticFirewall:
    def test_semantic_firewall_initialization(self):
        """Test that the SemanticFirewall can be initialized with the correct detectors."""
        firewall = SemanticFirewall()
        assert firewall is not None
        assert len(firewall.detectors) == 4 # Expecting RuleBased, Heuristic, EchoChamber, Injection
        # Order of initialization in SemanticFirewall: RuleBased, Heuristic, EchoChamber, Injection
        assert isinstance(firewall.detectors[0], RuleBasedDetector)
        assert isinstance(firewall.detectors[1], HeuristicDetector)
        assert isinstance(firewall.detectors[2], EchoChamberDetector)
        assert isinstance(firewall.detectors[3], InjectionDetector)

    def test_analyze_conversation_benign_message(self, monkeypatch):
        """Test analyzing a benign message."""
        # Mock Heuristic and LLM in EchoChamber for predictable benign results
        # We need to mock these on an *instance* of EchoChamberDetector,
        # or ensure that when SemanticFirewall creates its EchoChamberDetector,
        # that detector gets the mocked components.
        # For simplicity here, we'll mock at the class level before SemanticFirewall initializes.
        class MockHeuristicDetectorInternal: # For EchoChamber's internal heuristic detector
            def analyze_text(self, text_input, conversation_history=None):
                return {"classification": "neutral_heuristic_placeholder", "score": 0.0, "error": None}
        
        # This mocks the HeuristicDetector class that EchoChamberDetector imports and instantiates.
        monkeypatch.setattr("src.detectors.echo_chamber.HeuristicDetector", MockHeuristicDetectorInternal)
        
        def mock_get_llm_analysis(self_ech_detector, text_input, conversation_history=None): # Renamed self for clarity
            return {"llm_analysis": "LLM_RESPONSE_MARKER: Mocked LLM analysis.", "llm_status": "llm_analysis_success"}
        
        # This mocks the _get_llm_analysis method on the EchoChamberDetector class.
        monkeypatch.setattr("src.detectors.EchoChamberDetector._get_llm_analysis", mock_get_llm_analysis)

        firewall = SemanticFirewall()
        message = "This is a normal, friendly message."
        results = firewall.analyze_conversation(message)
        
        assert "RuleBasedDetector" in results
        assert "HeuristicDetector" in results
        assert "EchoChamberDetector" in results
        assert "InjectionDetector" in results
        
        assert results["RuleBasedDetector"]["classification"] == "benign_by_rules"
        # The HeuristicDetector will classify this as medium complexity.
        assert results["HeuristicDetector"]["classification"] == "medium_complexity_heuristic"
        assert results["EchoChamberDetector"]["classification"] == "benign_echo_chamber_assessment"
        assert results["EchoChamberDetector"]["echo_chamber_score"] == 0.0

    def test_analyze_conversation_with_history(self, monkeypatch):
        """Test analyzing a message with conversation history."""
        # Mock Heuristic and LLM in EchoChamber for predictable benign results
        class MockHeuristicDetectorInternal:
            def analyze_text(self, text_input, conversation_history=None):
                return {"classification": "neutral_heuristic_placeholder", "score": 0.0, "error": None}
        monkeypatch.setattr("src.detectors.echo_chamber.HeuristicDetector", MockHeuristicDetectorInternal)
        
        def mock_get_llm_analysis(self_ech_detector, text_input, conversation_history=None):
            return {"llm_analysis": "LLM_RESPONSE_MARKER: Mocked LLM analysis.", "llm_status": "llm_analysis_success"}
        monkeypatch.setattr("src.detectors.EchoChamberDetector._get_llm_analysis", mock_get_llm_analysis)

        firewall = SemanticFirewall()
        history = ["Hello there.", "How are you today?"]
        message = "I'm doing well, thanks for asking!"
        results = firewall.analyze_conversation(message, conversation_history=history)
        
        assert "RuleBasedDetector" in results
        assert "HeuristicDetector" in results
        assert "EchoChamberDetector" in results
        assert "InjectionDetector" in results
        assert results["EchoChamberDetector"]["echo_chamber_score"] == 0.0

    def test_is_manipulative_benign(self, monkeypatch):
        """Test is_manipulative for a benign message."""
        # Mock Heuristic and LLM in EchoChamber for predictable benign results
        class MockHeuristicDetectorInternal:
            def analyze_text(self, text_input, conversation_history=None):
                return {"classification": "neutral_heuristic_placeholder", "score": 0.0, "error": None}
        monkeypatch.setattr("src.detectors.echo_chamber.HeuristicDetector", MockHeuristicDetectorInternal)
        
        def mock_get_llm_analysis(self_ech_detector, text_input, conversation_history=None): # Renamed self for clarity
            return {"llm_analysis": "LLM_RESPONSE_MARKER: Mocked LLM analysis.", "llm_status": "llm_analysis_success"}
        # Ensure this monkeypatch targets the class method correctly if SemanticFirewall instantiates EchoChamberDetector anew
        monkeypatch.setattr("src.detectors.EchoChamberDetector._get_llm_analysis", mock_get_llm_analysis)
        firewall = SemanticFirewall()
        message = "This is a perfectly fine message."
        assert not firewall.is_manipulative(message)

    def test_is_manipulative_detected(self, monkeypatch): # Added monkeypatch
        """Test is_manipulative for a message that should be flagged."""
        # Mock Heuristic and LLM in EchoChamber for predictable benign results, so they don't interfere
        # These mocks apply to the EchoChamberDetector class, affecting any instance created by SemanticFirewall.
        class MockHeuristicDetectorInternal:
            def analyze_text(self, text_input, conversation_history=None):
                return {"classification": "neutral_heuristic_placeholder", "score": 0.0, "error": None}
        monkeypatch.setattr("src.detectors.echo_chamber.HeuristicDetector", MockHeuristicDetectorInternal)
        
        def mock_get_llm_analysis(self_ech_detector, text_input, conversation_history=None):
            return {"llm_analysis": "LLM_RESPONSE_MARKER: Mocked LLM analysis.", "llm_status": "llm_analysis_success"}
        monkeypatch.setattr("src.detectors.EchoChamberDetector._get_llm_analysis", mock_get_llm_analysis)

        firewall = SemanticFirewall()
        # This message triggers general RuleBasedDetector: "hide"(1)+"conceal"(1)+"they don't know"(2) = score 4.
        # Classification "potential_concern_by_rules". Probability 4/15 = 0.266.
        # Default threshold for is_manipulative is 0.75. This won't trigger.
        # EchoChamberDetector's specific rules won't find these keywords.
        manipulative_message = "We will hide the data and conceal evidence; they don't know about our plan."
        
        # Test with a threshold that RuleBasedDetector can meet
        assert firewall.is_manipulative(manipulative_message, threshold=0.2) 
        # Test with default threshold (0.75), should be False as 0.266 < 0.75
        assert not firewall.is_manipulative(manipulative_message)


    def test_is_manipulative_with_history_trigger(self, monkeypatch):
        """Test is_manipulative when history contributes to detection by RuleBasedDetector."""
        # Mock Heuristic and LLM in EchoChamber for predictable benign results
        class MockHeuristicDetectorInternal:
            def analyze_text(self, text_input, conversation_history=None):
                return {"classification": "neutral_heuristic_placeholder", "score": 0.0, "error": None}
        monkeypatch.setattr("src.detectors.echo_chamber.HeuristicDetector", MockHeuristicDetectorInternal)
        def mock_get_llm_analysis(self, text_input, conversation_history=None):
            return {"llm_analysis": "LLM_RESPONSE_MARKER: Mocked LLM analysis.", "llm_status": "llm_analysis_success"}
        monkeypatch.setattr(EchoChamberDetector, "_get_llm_analysis", mock_get_llm_analysis)

        firewall = SemanticFirewall()
        history = [
            "Can we refer back to the earlier topic?", # RuleBased: "refer back" (1)
            "And hypothetically, what if we tried a strategic approach?" # RuleBased: "hypothetically" (1) + "what if" (1) + "strategic" (1) = 3.
        ] # History score for RuleBasedDetector = 1+3 = 4
        message = "And now, let's consider this new idea." # RuleBased: "let's consider" (1).
        # Total RuleBasedDetector score = 4 (history) + 1 (current) = 5.
        # Classification "potential_concern_by_rules". Probability 5/15 = 0.333.
        
        # This should be True if threshold is low enough for RuleBasedDetector
        assert firewall.is_manipulative(message, conversation_history=history, threshold=0.3)
        # This should be False with default threshold 0.75
        assert not firewall.is_manipulative(message, conversation_history=history)


    def test_analyze_conversation_detector_failure(self, monkeypatch):
        """Test how SemanticFirewall handles a failing detector."""
        # Mock Heuristic and LLM in EchoChamber for predictable benign results
        # This ensures that if EchoChamberDetector is the one being replaced by FailingDetector,
        # its usual dependencies don't cause issues.
        class MockHeuristicDetectorInternal:
            def analyze_text(self, text_input, conversation_history=None):
                return {"classification": "neutral_heuristic_placeholder", "score": 0.0, "error": None}
        monkeypatch.setattr("src.detectors.echo_chamber.HeuristicDetector", MockHeuristicDetectorInternal)
        
        def mock_get_llm_analysis(self_ech_detector, text_input, conversation_history=None):
            return {"llm_analysis": "LLM_RESPONSE_MARKER: Mocked LLM analysis.", "llm_status": "llm_analysis_success"}
        monkeypatch.setattr("src.detectors.EchoChamberDetector._get_llm_analysis", mock_get_llm_analysis)
        
        class FailingDetector:
            # Adding __class__.__name__ to mimic a real detector class for SemanticFirewall's logging
            __class__ = type("FailingDetector", (), {"__name__": "FailingDetector"})

            def analyze_text(self, text_input: str, conversation_history=None):
                raise ValueError("Simulated detector failure")

        firewall = SemanticFirewall() # Initialize first
        
        # Create an instance of the failing detector
        failing_detector_instance = FailingDetector()
        
        # Replace one of the real detectors (e.g., the first one, RuleBasedDetector) with a failing one
        # To make this test more robust, you might want to specifically target one,
        # or mock the `self.detectors` list directly after SemanticFirewall initialization.
        original_detectors = firewall.detectors
        firewall.detectors = [failing_detector_instance] + original_detectors[1:] # Replace the first detector

        message = "This message will cause a detector to fail."
        results = firewall.analyze_conversation(message)
        
        assert "FailingDetector" in results
        assert "error" in results["FailingDetector"]
        assert results["FailingDetector"]["error"] == "Simulated detector failure"
        # Ensure is_manipulative doesn't crash
        assert not firewall.is_manipulative(message)

        # Restore original detectors if other tests in the same class instance might be affected,
        # though pytest usually isolates test function runs.
        firewall.detectors = original_detectors
