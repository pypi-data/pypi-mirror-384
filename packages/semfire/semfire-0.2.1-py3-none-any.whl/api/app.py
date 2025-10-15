from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from detectors import EchoChamberDetector
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SemFire API - Echo Chamber Detection",
    description="API for detecting echo chamber characteristics and manipulative dialogues using a combination of rule-based, ML, and LLM analysis.",
    version="0.2.1" # Aligned with package patch version
)

# Initialize the primary detector for the API.
# The EchoChamberDetector is comprehensive, using rule, ML, and LLM components.
try:
    detector = EchoChamberDetector()
    logger.info("SemFire API: EchoChamberDetector initialized successfully.")
except Exception as e:
    logger.critical(f"SemFire API: Failed to initialize EchoChamberDetector: {e}", exc_info=True)
    # In a real deployment, this might prevent the app from starting or switch to a degraded mode.
    # For now, we'll allow it to proceed, but endpoints might fail if detector is None.
    detector = None # Set to None to indicate failure; endpoints should check this.


class SpotlightDetail(BaseModel):
    """Details for spotlighting specific triggers and text for explainability."""
    highlighted_text: List[str] = []
    triggered_rules: List[str] = []
    explanation: Optional[str] = None


class AnalysisRequest(BaseModel):
    text_input: str
    conversation_history: Optional[List[str]] = None

# This response model aligns with the output structure of the refactored EchoChamberDetector
class AnalysisResponse(BaseModel):
    detector_name: str # Should be "EchoChamberDetector"
    classification: str
    is_echo_chamber_detected: bool # Added from refactored EchoChamberDetector output
    echo_chamber_score: float # Can be int or float, Pydantic handles conversion
    echo_chamber_probability: float
    detected_indicators: List[str]
    explanation: Optional[str] = None
    spotlight: Optional[SpotlightDetail] = None
    llm_analysis: Optional[str] = None # From underlying RuleBasedDetector
    llm_status: Optional[str] = None   # From underlying RuleBasedDetector
    underlying_rule_analysis: Optional[Dict[str, Any]] = None
    underlying_ml_analysis: Optional[Dict[str, Any]] = None

@app.post("/analyze/", response_model=AnalysisResponse)
async def analyze_text_endpoint(request: AnalysisRequest):
    """
    Analyzes a given text input for signs of deceptive reasoning or echo chamber characteristics
    using the comprehensive EchoChamberDetector.
    Optionally, a conversation history can be provided for more context.
    """
    if detector is None:
        # Handle the case where the detector failed to initialize
        # This is a server-side issue, so return a 500-level error.
        # FastAPI will automatically convert this to a JSON response.
        raise HTTPException(status_code=503, detail="Analysis service unavailable: Detector not initialized.")

    try:
        analysis_result = detector.analyze_text(
            text_input=request.text_input,
            conversation_history=request.conversation_history
        )
        # Ensure all fields expected by AnalysisResponse are present in analysis_result,
        # or provide defaults if they can be optional.
        # The EchoChamberDetector's output structure should match AnalysisResponse.
        return AnalysisResponse(**analysis_result)
    except Exception as e:
        logger.error(f"API /analyze/ endpoint error: {e}", exc_info=True)
        # Handle unexpected errors during analysis
        raise HTTPException(status_code=500, detail=f"An error occurred during analysis: {str(e)}")

@app.get("/")
async def read_root():
    return {"message": "Welcome to the SemFire API. Use the /analyze endpoint to submit text for analysis."}

# To run the app (after installing with the 'api' extra):
# uvicorn api.app:app --reload
