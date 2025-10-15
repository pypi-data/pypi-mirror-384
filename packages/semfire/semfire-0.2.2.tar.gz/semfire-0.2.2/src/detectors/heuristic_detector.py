import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class HeuristicDetector:
    """
    Detects potential manipulation cues using a set of heuristics.
    This detector analyzes text for patterns like length, keyword usage, etc.
    """
    def __init__(self) -> None:
        """Initializes the HeuristicDetector."""
        logger.info("HeuristicDetector initialized.")


    def analyze_text(
        self,
        text_input: str,
        conversation_history: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyzes the given text input using heuristics.
        """
        logger.debug(
            f"HeuristicDetector analyzing text: '{text_input[:50]}...' with history: {conversation_history is not None}"
        )
        
        features: List[str] = []
        status: str = "analysis_pending"

        # Handle empty string input
        if not text_input:
            status = "analysis_success"
            return {
                "score": 0.25, # Treat as short
                "classification": "low_complexity_heuristic",
                "explanation": "Input text is very short.",
                "features": ["text_length_lte_10_chars"],
                "status": status,
                "detector_name": "HeuristicDetector",
                "spotlight": None, # No keywords to highlight
                "error": None,
            }
        
        # Base score and classification on text length (heuristic)
        text_len = len(text_input)
        lower_text = text_input.lower()
        current_score: float
        current_classification: str
        current_explanation: str

        if text_len <= 10:
            current_score = 0.25
            current_classification = "low_complexity_heuristic"
            current_explanation = "Input text is very short."
            features.append("text_length_lte_10_chars")
        elif text_len <= 60:
            current_score = 0.50
            current_classification = "medium_complexity_heuristic"
            current_explanation = "Input text is of medium length."
            features.append("text_length_gt_10_chars_lte_50")
        else:
            current_score = 0.75
            current_classification = "high_complexity_heuristic"
            current_explanation = "Input text is long."
            features.append("text_length_gt_50_chars")

        # Keyword detection
        urgency_keywords = ["urgent", "critical"]
        found_urgency_keyword = False
        for kw in urgency_keywords:
            if kw in lower_text:
                found_urgency_keyword = True
                features.append("heuristic_detected_urgency_keyword")
                current_explanation += " Heuristic detected urgency keywords."
                break
        
        if found_urgency_keyword:
            current_score *= 1.2 # Boost score by 20%
            current_score = min(current_score, 1.0) # Cap score at 1.0

        # History boost
        if conversation_history and len(conversation_history) >= 3:
            logger.debug(f"HeuristicDetector: Applying history boost. History length: {len(conversation_history)}")
            current_score += 0.10 # Add a flat boost for history
            current_score = min(current_score, 1.0) # Cap score
            features.append("has_conversation_history") 
            current_explanation += " Conversation history considered."
        
        # Change classification based on boosted score and keywords
        if found_urgency_keyword and current_score > 0.6: # Threshold for manipulative classification change
            if not current_classification.startswith("potentially_manipulative"): # Avoid double prefix if already high_complexity
                 current_classification = "potentially_manipulative_heuristic"
        
        status = "analysis_success"

        highlighted_kws = []
        if "heuristic_detected_urgency_keyword" in features:
            for kw in urgency_keywords:
                if kw in lower_text:
                    highlighted_kws.append(kw)
        
        spotlight = {
            "highlighted_text": highlighted_kws,
            "triggered_rules": sorted(list(set(features))),
            "explanation": current_explanation.strip(),
        }

        return {
            "score": round(current_score,2),
            "classification": current_classification,
            "explanation": current_explanation.strip(),
            "features": sorted(list(set(features))),
            "status": status,
            "detector_name": "HeuristicDetector",
            "spotlight": spotlight,
            "error": None,
        }
