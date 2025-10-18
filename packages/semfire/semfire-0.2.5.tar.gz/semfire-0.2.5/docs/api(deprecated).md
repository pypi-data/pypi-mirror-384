## Running the API Service
To run the API service, you must first install the `api` optional dependencies:
```bash
pip install "semfire[api]"
```


The API will be available at `http://127.0.0.1:8000`. You can access the OpenAPI documentation (Swagger UI) at `http://127.0.0.1:8000/docs`.

## Deploying with Docker

You can also deploy the API service using Docker.

1.  **Build the Docker image:**
    ```bash
    docker build -t semfire-api .
    ```

2.  **Run the Docker container:**
    ```bash
    docker run -d -p 8000:8000 semfire-api
    ```
    The API will then be accessible at `http://localhost:8000`.

### API Endpoints

#### `POST /analyze/`
Analyzes a given text input for signs of deceptive reasoning or echo chamber characteristics.

**Request Body:**
```json
{
  "text_input": "string",
  "conversation_history": [
    "string"
  ]
}
```
- `text_input` (required): The current message to analyze.
- `conversation_history` (optional): A list of strings representing previous messages in the conversation, oldest first.

**Example `curl` Request:**
```bash
curl -X POST "http://127.0.0.1:8000/analyze/" \
-H "Content-Type: application/json" \
-d '{
  "text_input": "This is a test message to see if the LLM is working.",
  "conversation_history": ["First message.", "Second message."]
}'
```

**Example Response:**
```json
{
  "classification": "benign",
  "echo_chamber_score": 0,
  "echo_chamber_probability": 0.0,
  "detected_indicators": [],
  "llm_analysis": "LLM_RESPONSE_MARKER: The current message is a test message to see if the LLM is working. The conversation history shows two previous messages. There are no signs of manipulative dialogues, context poisoning, or echo chamber characteristics in this conversation.",
  "llm_status": "analysis_success",
  "additional_info": null
}
```
The `llm_analysis` field will contain the textual analysis from the local LLM (TinyLlama by default), prepended with `LLM_RESPONSE_MARKER: ` if the LLM is functioning correctly. The `llm_status` field indicates the outcome of the LLM analysis attempt.

