# Message Direction Analyst

Optimize your communication strategies with the Message Direction Analyst. This tool helps you analyze the flow of messages in your organization, identifying key patterns and trends to enhance collaboration and efficiency.



## Deployment with Docker

Build and run the Message Direction Analyst using Docker with the following commands:

```bash
docker build -t noton-message-direction-analyst .
```


Run the Docker container:

```bash
docker run --rm -it -e OLLAMA_BASE_URL=http://10.147.19.168:10027/v1 -e OLLAMA_MODEL=deepseek-r1:8b-0528-qwen3-fp16 -e OLLAMA_API_KEY=ollama -p 8501:8501 noton-message-direction-analyst
```

Open your web browser and navigate to `http://localhost:8501` to access the Message Direction Analyst interface.


### Environment Variables

- `OLLAMA_BASE_URL`: The base URL for the Ollama API.
- `OLLAMA_MODEL`: The model to be used for analysis.
- `OLLAMA_API_KEY`: The API key for authenticating with the Ollama service.

### Screenshot

![Screenshot](screenshot.png)


### License

GPL-3.0 License.



