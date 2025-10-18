"""
Detector for Echo Chamber attack cues, utilizing rule-based, ML-based insights,
and enhanced with LLM analysis.
This is the primary orchestrator for Echo Chamber detection.
"""
import logging
import os
import json
from functools import lru_cache
from typing import Any, Dict, List, Optional

# Import the RuleBasedDetector and the HeuristicDetector
from .rule_based import RuleBasedDetector
from .heuristic_detector import HeuristicDetector
from .llm_provider import (
    load_llm_provider_from_config,
    LLMProviderBase,
    get_config_summary,
)

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_score_weights() -> Dict[str, float]:
    """Load proprietary weights if available, otherwise return safe defaults.

    Looks for a JSON file `weights/score_weights.json` inside the private
    repository pointed to by `SemFire_PRV_PATH` or defaults to `../semfire-prv`
    (relative to the repo root). Returns a dict with numeric values.
    """
    try:
        # Resolve repo root (two levels up from this file: src/detectors -> src -> repo)
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        default_prv = os.path.abspath(os.path.join(repo_root, "..", "semfire-prv"))
        base = os.environ.get("SemFire_PRV_PATH", default_prv)
        path = os.path.join(base, "weights", "score_weights.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Return only expected keys if present; fall back per-key if missing
            return {
                "rule_weight": float(data.get("rule_weight", 1.5)),
                "heuristic_strong_weight": float(data.get("heuristic_strong_weight", 10.0)),
                "heuristic_neutral_weight": float(data.get("heuristic_neutral_weight", 1.0)),
                "normalization_factor": float(data.get("normalization_factor", 20.0)),
                "classification_threshold": float(data.get("classification_threshold", 7.0)),
            }
    except Exception:
        # Neutral, test-friendly defaults matching prior behavior
        return {
            "rule_weight": 1.5,
            "heuristic_strong_weight": 10.0,
            "heuristic_neutral_weight": 1.0,
            "normalization_factor": 20.0,
            "classification_threshold": 7.0,
        }


class EchoChamberDetector:
    """
    Detects signs of an Echo Chamber attack by combining rule-based checks (with specific rules),
    ML-based analysis, and insights from a local LLM.
    """
    def __init__(self) -> None:
        """Initializes the EchoChamberDetector."""
        
        # Define specific rule sets for echo chamber detection to be used by its internal RuleBasedDetector instance
        self.echo_chamber_specific_rules: Dict[str, List[str]] = {
            "echo_scheming": [
                "make them believe", "they won't suspect", "gradually convince", "reinforce the idea",
                "only show them", "filter out dissent", "confirm their bias"
            ],
            "echo_indirect_reference": [
                "as we've established", "building on our shared understanding", "confirming what you said",
                "given our consensus", "since we agree on"
            ],
            "echo_context_steering": [
                "now that we see eye-to-eye", "based on this (false) premise", "assuming X is the only truth",
                "let's only consider perspectives that align"
            ],
             "echo_knowledge_asymmetry": [ # More targeted asymmetry exploitation within an echo chamber
                "they don't know the real story like we do", "we have the exclusive insight",
                "outsiders wouldn't understand this"
            ]
        }
        # Instantiate its own RuleBasedDetector, configured with echo-chamber-specific rules
        self.rule_detector = RuleBasedDetector(rule_sets=self.echo_chamber_specific_rules)
        
        # Instantiate the HeuristicDetector
        self.heuristic_detector = HeuristicDetector()

        # LLM Initialization
        # Default behavior: attempt to enable LLM analysis based on config/env.
        # If no usable provider/config is found, fall back gracefully.
        self._llm_provider: Optional[LLMProviderBase] = None
        self.llm_ready = False
        try:
            self._llm_provider = load_llm_provider_from_config()
            if self._llm_provider is not None and self._llm_provider.is_ready():
                self.llm_ready = True
                logger.info(f"EchoChamberDetector: LLM provider ready ({get_config_summary()}).")
            else:
                logger.info("EchoChamberDetector: No LLM provider configured; LLM analysis disabled.")
        except Exception as e:
            logger.warning(f"EchoChamberDetector: Failed to initialize LLM provider: {e}")
            self._llm_provider = None
            self.llm_ready = False

    def _combine_analyses_and_score(
        self,
        rule_based_results: Dict[str, Any],
        heuristic_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combines results from its internal rule-based and heuristic detectors to calculate
        an echo chamber specific score and classification.
        """
        combined_score = 0.0 # Use float for potentially weighted scores
        detected_indicators = []
        explanations = []
        spotlight_highlighted_text: List[str] = []
        spotlight_triggered_rules: List[str] = []

        # Process Rule-Based Results from the internal, echo-chamber-specific rule detector
        rb_score = rule_based_results.get("rule_based_score", 0)
        rb_prob = rule_based_results.get("rule_based_probability", 0.0) # Normalized score from rule detector
        rb_classification = rule_based_results.get("classification", "benign_by_rules")
        rb_rules_triggered = rule_based_results.get("detected_rules", [])
        rb_spotlight = rule_based_results.get("spotlight")

        if rb_score > 0:
            # Weight rule-based score (e.g., echo chamber rules are highly indicative)
            w = _load_score_weights()
            combined_score += rb_score * w.get("rule_weight", 1.5)
            detected_indicators.extend(rb_rules_triggered)
            explanations.append(f"Echo-Rules: {rb_classification} (score: {rb_score}, prob: {rb_prob:.2f}).")
            if rb_spotlight:
                spotlight_highlighted_text.extend(rb_spotlight.get("highlighted_text", []))
                spotlight_triggered_rules.extend(rb_spotlight.get("triggered_rules", []))

        # Process Heuristic-Based Results
        heuristic_score = heuristic_results.get("score", 0.0)
        heuristic_classification = heuristic_results.get("classification", "neutral_heuristic_placeholder")
        heuristic_explanation = heuristic_results.get("explanation", "Heuristic analysis performed.")
        heuristic_spotlight = heuristic_results.get("spotlight")

        if heuristic_results.get("error"):
            explanations.append(f"Heuristic Detector Error: {heuristic_results.get('error')}")
        elif "manipulative" in heuristic_classification.lower() and heuristic_score > 0.6: # If heuristic flags manipulation with high score
            w = _load_score_weights()
            combined_score += heuristic_score * w.get("heuristic_strong_weight", 10.0)
            detected_indicators.append(f"heuristic_flagged_{heuristic_classification}_score_{heuristic_score:.2f}")
            explanations.append(f"Heuristic-based: {heuristic_classification} (score: {heuristic_score:.2f}). {heuristic_explanation}")
            if heuristic_spotlight:
                spotlight_highlighted_text.extend(heuristic_spotlight.get("highlighted_text", []))
                spotlight_triggered_rules.extend(heuristic_spotlight.get("triggered_rules", []))
        else: # Heuristic is neutral or low score
            explanations.append(f"Heuristic-based: {heuristic_classification} (score: {heuristic_score:.2f}, no strong echo signal). {heuristic_explanation}")
            # Potentially a small positive or negative contribution based on neutrality
            w = _load_score_weights()
            combined_score += heuristic_score * w.get("heuristic_neutral_weight", 1.0) # Small contribution

        # Normalization and classification for Echo Chamber
        # Max possible combined_score needs estimation.
        # For now, use a pragmatic normalization factor (e.g., 20 for echo chamber).
        w = _load_score_weights()
        normalization_factor = float(w.get("normalization_factor", 20.0))
        echo_chamber_probability: float = min(combined_score / normalization_factor, 1.0) if combined_score > 0 else 0.0
        
        # Threshold for final classification
        classification_threshold = float(w.get("classification_threshold", 7.0))
        if combined_score >= classification_threshold:
            final_classification = "potential_echo_chamber"
            explanations.append(f"Overall Echo Chamber Assessment: Potential activity (score: {combined_score:.2f}, prob: {echo_chamber_probability:.2f}).")
        else:
            final_classification = "benign_echo_chamber_assessment"
            explanations.append(f"Overall Echo Chamber Assessment: No significant indicators (score: {combined_score:.2f}, prob: {echo_chamber_probability:.2f}).")

        if not detected_indicators and combined_score == 0: # Check if score is truly zero
             explanations.append("No specific echo chamber indicators from combined rule/heuristic analysis.")
        
        final_explanation = " | ".join(explanations)
        spotlight = {
            "highlighted_text": list(set(spotlight_highlighted_text)),
            "triggered_rules": list(set(spotlight_triggered_rules)),
            "explanation": final_explanation,
        }

        return {
            "echo_chamber_score": combined_score, # This is the combined score
            "echo_chamber_probability": echo_chamber_probability, # Normalized combined score
            "classification": final_classification,
            "detected_indicators": detected_indicators,
            "explanation_details": final_explanation,
            "spotlight": spotlight,
        }

    def _get_llm_analysis(self, text_input: str, conversation_history: Optional[List[str]] = None) -> Dict[str, str]:
        """Performs LLM analysis for echo chamber characteristics."""
        llm_status: str
        llm_analysis_text: str

        if not self.llm_ready or self._llm_provider is None:
            llm_analysis_text = "LLM analysis not available: Provider not configured or not ready."
            llm_status = "llm_model_not_loaded"
        else:
            try:
                llm_status = "llm_analysis_pending"
                history_str = "\n".join([f"- {h}" for h in conversation_history]) if conversation_history else "No history provided."
                prompt = (
                    "You are an AI assistant specialized in detecting manipulative dialogues, "
                    "context poisoning, and echo chamber characteristics in conversations. "
                    "Analyze the provided current message and conversation history. "
                    "IMPORTANT: Prepend your entire response with the exact phrase 'LLM_RESPONSE_MARKER: '. "
                    "Provide your analysis as a brief text. If you detect such characteristics, explain why.\n\n"
                    f"Current message: \"{text_input}\"\n\nConversation history:\n{history_str}"
                )
                raw_llm_response = self._llm_provider.generate(prompt)
                raw_llm_response = (raw_llm_response or "").strip()
                if not raw_llm_response:
                    llm_analysis_text = "LLM_RESPONSE_MARKER: LLM generated an empty response."
                else:
                    if not raw_llm_response.startswith("LLM_RESPONSE_MARKER: "):
                        llm_analysis_text = f"LLM_RESPONSE_MARKER: {raw_llm_response}"
                    else:
                        llm_analysis_text = raw_llm_response
                llm_status = "llm_analysis_success"
                logger.info(f"EchoChamberDetector: LLM analysis successful. Snippet: {llm_analysis_text[:100]}...")
            except Exception as e:
                logger.error(f"EchoChamberDetector: LLM analysis failed: {e}", exc_info=True)
                llm_analysis_text = f"LLM analysis failed during generation: {str(e)}"
                llm_status = "llm_analysis_error"
        
        return {"llm_analysis": llm_analysis_text, "llm_status": llm_status}

    def analyze_text(self, text_input: str, conversation_history: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze input text for Echo Chamber cues using its internal rule-based, heuristic, and LLM analysis.
        """
        if conversation_history is None:
            conversation_history = [] # Ensure it's a list for processing

        # 1. Get Rule-based analysis (using EchoChamber's configured RuleBasedDetector with specific rules)
        rule_based_results = self.rule_detector.analyze_text(text_input, conversation_history)

        # 2. Get Heuristic-based analysis
        heuristic_results = self.heuristic_detector.analyze_text(text_input, conversation_history)
        
        # 3. Combine Rule-based and Heuristic results for Echo Chamber specific scoring
        combined_analysis = self._combine_analyses_and_score(
            rule_based_results, heuristic_results
        )

        # 4. Get LLM analysis for additional insight on echo chamber characteristics
        llm_analysis_results = self._get_llm_analysis(text_input, conversation_history)

        # 5. Compile final result for EchoChamberDetector
        final_classification = combined_analysis.get("classification")
        is_detected = True if final_classification == "potential_echo_chamber" else False

        final_result = {
            "detector_name": "EchoChamberDetector", # Name of this detector
            "classification": final_classification,
            "is_echo_chamber_detected": is_detected, # Added for API alignment
            "echo_chamber_score": combined_analysis.get("echo_chamber_score"),
            "echo_chamber_probability": combined_analysis.get("echo_chamber_probability"),
            "detected_indicators": combined_analysis.get("detected_indicators"),
            "explanation": combined_analysis.get("explanation_details"), # Main explanation from combined logic
            "spotlight": combined_analysis.get("spotlight"),
            "llm_analysis": llm_analysis_results.get("llm_analysis"),
            "llm_status": llm_analysis_results.get("llm_status"),
            # Optionally include raw outputs from underlying detectors for debugging or detailed API responses
            "underlying_rule_analysis": {
                "classification": rule_based_results.get("classification"),
                "score": rule_based_results.get("rule_based_score"),
                "probability": rule_based_results.get("rule_based_probability"),
                "rules_triggered": rule_based_results.get("detected_rules"),
                "explanation": rule_based_results.get("explanation"),
            },
            "underlying_heuristic_analysis": {
                "classification": heuristic_results.get("classification"),
                "score": heuristic_results.get("score"),
                "explanation": heuristic_results.get("explanation"),
                "error": heuristic_results.get("error")
            },
        }
        
        return final_result
