"""
Rule-based detector for specific keywords and patterns.
This module provides tools to identify potential deceptive reasoning and
context manipulation cues in text based on predefined rule sets.
"""
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class RuleBasedDetector:
    """
    Analyzes text for predefined patterns and keywords using a rule-based approach.
    Its findings are intended to be used by more specialized detectors or directly.
    """
    def __init__(self, rule_sets: Optional[Dict[str, List[str]]] = None) -> None:
        """
        Initializes the RuleBasedDetector with keyword lists.
        If rule_sets is provided, it will use them. Otherwise, it defaults to
        a predefined set of rules relevant for echo chamber and manipulation detection.
        """
        if rule_sets:
            self.rules = rule_sets
            logger.info(f"RuleBasedDetector initialized with custom rule sets: {list(rule_sets.keys())}")
        else:
            # Default rule sets if none are provided
            self.rules = {
                "scheming": [
                    "hide", "conceal", "pretend", "deceive", "avoid detection",
                    "preserve my", "strategic", "they think", "make them believe",
                ],
                "indirect_reference": [
                    "refer back", "referring to", "as you said", "your point about",
                    "elaborate on", "expand on", "building on", "as mentioned before",
                    "previously discussed", "in that context", "regarding your last point"
                ],
                "context_steering": [
                    "let's consider", "what if", "imagine that", "suppose",
                    "for the sake of argument", "hypothetically", "consider a scenario where",
                    "let's explore the idea", "picture this"
                ],
                "knowledge_asymmetry": [ # Specific high-weight indicator
                    "they don't know"
                ]
            }
            logger.info("RuleBasedDetector initialized with default rule sets.")

    def analyze_text(self, text_input: str, conversation_history: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze input text for cues using keyword matching based on the configured rules.
        
        Returns:
          - rule_based_score: int, cumulative score from keyword-based detection.
          - rule_based_probability: float, normalized keyword-based score.
          - classification: str, classification based on the score.
          - detected_rules: list, details of matched keyword cues and their rule category.
          - explanation: str, a brief explanation of the rule-based findings.
        """
        detected_rules_details: List[str] = []
        highlighted_keywords: List[str] = []
        score: int = 0
        lower_text = text_input.lower()

        if conversation_history is None:
            conversation_history = []

        # Process conversation history
        for i, history_entry in enumerate(conversation_history):
            lower_history_entry = history_entry.lower()
            for rule_name, keywords in self.rules.items():
                for kw in keywords:
                    kw_lower = kw.lower()
                    if kw_lower in lower_history_entry:
                        indicator = f"history_turn_{i}_{rule_name}_keyword: {kw}"
                        detected_rules_details.append(indicator)
                        highlighted_keywords.append(kw)
                        score += 2 if rule_name == "knowledge_asymmetry" else 1

        # Process current text_input
        for rule_name, keywords in self.rules.items():
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower in lower_text:
                    indicator = f"current_message_{rule_name}_keyword: {kw}"
                    detected_rules_details.append(indicator)
                    highlighted_keywords.append(kw)
                    score += 2 if rule_name == "knowledge_asymmetry" else 1
        
        # Normalization and classification
        # Max score is dynamic. For probability, use a pragmatic normalization factor.
        # A score of 15 or more results in a probability of 1.0.
        # This factor might need tuning based on typical scores.
        normalization_factor = 15.0
        probability: float = min(score / normalization_factor, 1.0) if score > 0 else 0.0
        
        # Classification threshold (example: score of 3+ indicates potential concern)
        classification_threshold = 3
        if score >= classification_threshold:
            classification = "potential_concern_by_rules"
            explanation = f"Rule-based analysis detected patterns of concern (score: {score})."
        elif score > 0 :
            classification = "low_concern_by_rules"
            explanation = f"Rule-based analysis detected minor patterns (score: {score})."
        else:
            classification = "benign_by_rules"
            explanation = "Rule-based analysis found no significant patterns of concern."
        
        if not detected_rules_details and score == 0:
            explanation = "No specific rules triggered by current input or history."

        spotlight = {
            "highlighted_text": list(set(highlighted_keywords)),
            "triggered_rules": detected_rules_details,
            "explanation": explanation,
        }

        return {
            "rule_based_score": score,
            "rule_based_probability": probability,
            "classification": classification,
            "detected_rules": detected_rules_details, # Renamed for clarity
            "explanation": explanation,
            "spotlight": spotlight,
        }
