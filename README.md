# Message Direction Analyst

Message Direction Analyst is a Streamlit application, backed by an Ollama-compatible LLM, that helps you reshape any draft into a focused, audience-aware narrative. A built‑in REST API keeps the UI and machine clients in sync, so every refinement path is reproducible.


## Highlights

- **Immersive creation surface** – dual-pane workspace with contextual metrics, guidance hints, and saved history.
- **Flexible controls** – tone sliders, direction presets, empathy/action toggles, and custom focus chips inform a structured analyst prompt.
- **First-class API** – the Streamlit UI calls the same `/api/analyze` endpoint you can hit from automation scripts or other services.


## Quick Start (Docker)

### 1. Build the image

```bash
docker build -t noton-message-direction-analyst .
```

### 2. Run the container

```bash
docker run --rm -it \
  -e OLLAMA_BASE_URL=http://<ollama-host>:<ollama-port>/v1 \
  -e OLLAMA_MODEL=deepseek-r1:8b-0528-qwen3-fp16 \
  -e OLLAMA_API_KEY=ollama \
  -e MESSAGE_ANALYST_API_URL=http://<host-ip>:8052 \
  -p 8051:8501 \  # Streamlit UI
  -p 8052:8601 \  # REST API
  noton-message-direction-analyst
```

Replace the placeholders with your own endpoints. `MESSAGE_ANALYST_API_URL` should point to the host/IP that clients (including the Streamlit app running inside the container) will use to reach the REST service.

### 3. Access the app

Open `http://localhost:8051` (or the host/IP you mapped) to launch the redesigned interface.


## REST API

Every UI run hits the same public endpoint, so you can trigger analyses without the browser:

- **POST** `${MESSAGE_ANALYST_API_URL:-http://127.0.0.1:8052}/api/analyze`
- **Body**

```json
{
  "query": "Draft a note to my team thanking them for the last release."
}
```

- **Sample response**

```json
{
  "query": "Draft a note to my team thanking them for the last release.",
  "response": "Team, thank you for the focus and resilience you brought to the last release...",
  "meta": {
    "took_ms": 2150.71
  }
}
```

This response shape is identical to what the Streamlit UI consumes, making it safe to automate testing, trigger batch rewrites, or integrate with chat platforms.


## Configuration

| Variable | Description | Default |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | Base URL for your Ollama/OpenAI-compatible endpoint. | `http://localhost:11434/v1` |
| `OLLAMA_MODEL` | Model ID to query. | `deepseek-r1:8b-0528-qwen3-fp16` |
| `OLLAMA_API_KEY` | API key for the LLM provider (optional for unsecured local Ollama). | `ollama` |
| `MESSAGE_ANALYST_API_HOST` | REST binding address inside the container. | `0.0.0.0` |
| `MESSAGE_ANALYST_API_PORT` | REST port inside the container. | `8601` |
| `MESSAGE_ANALYST_API_URL` | Public URL (host/IP + port) that clients should use when calling the REST API. Overrides the default `http://127.0.0.1:<port>`. | computed |


## Modern Web Experience

- Immersive hero section with contextual cues keeps the app grounded on objectives instead of UI clutter.
- Live metrics and guidance hints reflect word count, sentence balance, and control selections in real time.
- History view, copy-to-clipboard, and prompt previews make it simple to audit past runs or reuse outputs.


## Screenshot

![Screenshot](screenshot.png)


## License

GPL-3.0 License.
