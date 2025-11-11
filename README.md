# Message Direction Analyst

Optimize your communication strategies with the Message Direction Analyst. This tool helps you analyze the flow of messages in your organization, identifying key patterns and trends to enhance collaboration and efficiency.



## Deployment with Docker

Build and run the Message Direction Analyst using Docker with the following commands:

```bash
docker build -t noton-message-direction-analyst .
```

Run the Docker container (example below keeps the UI reachable on `http://192.168.1.197:8051`
and exposes the REST API on `http://192.168.1.197:8052`, in which `192.168.1.197` is my ip address):

```bash
docker run --rm -it \
  -e OLLAMA_BASE_URL=http://10.147.19.168:10027/v1 \
  -e OLLAMA_MODEL=deepseek-r1:8b-0528-qwen3-fp16 \
  -e OLLAMA_API_KEY=ollama \
  -e MESSAGE_ANALYST_API_URL=http://192.168.1.197:8052 \
  -p 8051:8501 \
  -p 8052:8601 \
  noton-message-direction-analyst
```

in which `http://10.147.19.168:10027/v1` is my self-hosted Ollama server address, `deepseek-r1:8b-0528-qwen3-fp16` is the model I use, and `ollama` is my API key.
In case you would prefer to use OpenAI or OpenRouter, set the `OLLAMA_BASE_URL` and `OLLAMA_API_KEY` accordingly.
I set the `MESSAGE_ANALYST_API_URL` to point to my host IP so that the Streamlit UI inside the container can reach the REST API endpoint.


Open your web browser and navigate to `http://localhost:8051` (or `http://192.168.1.197:8051` in my case) to access the Message Direction Analyst interface.


### REST API

The application now exposes a lightweight REST endpoint alongside the Streamlit UI. The UI itself consumes this endpoint, so any automation can share the exact same interface:

- **POST** `${MESSAGE_ANALYST_API_URL:-http://127.0.0.1:8052}/api/analyze`

**Body**

```json
{
  "query": "Draft a note to my team thanking them for the last release."
}
```

**Sample response**

```json
{
  "query": "Draft a note to my team thanking them for the last release.",
  "response": "Team, thank you for the focus and resilience you brought to the last release...",
  "meta": {
    "took_ms": 2150.71
  }
}
```

Environment variables for the API:

- `MESSAGE_ANALYST_API_HOST` (default `0.0.0.0`): bind address inside the container.
- `MESSAGE_ANALYST_API_PORT` (default `8601`): listening port inside the container.
- `MESSAGE_ANALYST_API_URL` (default `http://127.0.0.1:<port>`): base URL the Streamlit process (and your clients) should use when calling the API. Override this if the HTTP endpoint is served behind a proxy/load balancer.


### Modern Web Experience

- Immersive hero section with contextual tips and dynamic progress cues keeps the UI focused on essentials.
- Dual-pane layout separates briefing controls from live diagnostics, tightening the feedback loop as you type.
- Optional tone, direction, length, empathy, and action toggles inform the backend prompt so REST clients receive consistent guidance.
- Built-in history view plus copy-to-clipboard makes it easy to reuse refined narratives or audit recent analyses.


### Environment Variables

- `OLLAMA_BASE_URL`: The base URL for the Ollama API.
- `OLLAMA_MODEL`: The model to be used for analysis.
- `OLLAMA_API_KEY`: The API key for authenticating with the Ollama service, optional for self-hosted Ollama server.
- `MESSAGE_ANALYST_API_HOST`: Host interface for the REST server.
- `MESSAGE_ANALYST_API_PORT`: (Optional) Port for the REST server.
- `MESSAGE_ANALYST_API_URL`: (Optional) Base URL used by the Streamlit UI/API clients.

### Screenshot

![Screenshot](screenshot.png)


### License

GPL-3.0 License.
