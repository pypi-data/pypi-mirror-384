import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Mock the detector *before* it is imported by the app module because the
# detector is initialized at the module level.
mock_detector_instance = MagicMock()
mock_detector_instance.analyze_text.return_value = {
    "detector_name": "EchoChamberDetector",
    "classification": "mocked_classification",
    "is_echo_chamber_detected": False,
    "echo_chamber_score": 0.5,
    "echo_chamber_probability": 0.5,
    "detected_indicators": ["mocked_indicator"],
    "explanation": "Mocked explanation",
    "spotlight": {
        "highlighted_text": ["mocked"],
        "triggered_rules": ["mocked_rule"],
        "explanation": "Mocked spotlight explanation"
    },
    "llm_analysis": "mocked llm analysis",
    "llm_status": "llm_analysis_success",
    "underlying_rule_analysis": {},
    "underlying_ml_analysis": {}
}

# The patch targets where `EchoChamberDetector` is looked up in `api.app`.
with patch('detectors.EchoChamberDetector', return_value=mock_detector_instance):
    from api.app import app

client = TestClient(app)


def test_read_root():
    """Tests the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the SemFire API. Use the /analyze endpoint to submit text for analysis."}


def test_analyze_text_endpoint():
    """Tests the /analyze endpoint with a standard request."""
    request_data = {
        "text_input": "This is a test.",
        "conversation_history": ["A previous message."]
    }
    response = client.post("/analyze/", json=request_data)

    assert response.status_code == 200
    mock_detector_instance.analyze_text.assert_called_once_with(
        text_input="This is a test.",
        conversation_history=["A previous message."]
    )
    response_json = response.json()
    assert response_json["classification"] == "mocked_classification"
    assert response_json["echo_chamber_score"] == 0.5


def test_analyze_text_no_history():
    """Tests the /analyze endpoint with no conversation history."""
    mock_detector_instance.reset_mock() # Reset mock for a clean call
    request_data = {"text_input": "Another test."}
    response = client.post("/analyze/", json=request_data)

    assert response.status_code == 200
    mock_detector_instance.analyze_text.assert_called_with(
        text_input="Another test.",
        conversation_history=None
    )


@patch('api.app.detector', None)
def test_detector_not_initialized():
    """Tests the API's error handling when the detector fails to initialize."""
    request_data = {"text_input": "test"}
    response = client.post("/analyze/", json=request_data)
    assert response.status_code == 503
    assert "Detector not initialized" in response.json()["detail"]
