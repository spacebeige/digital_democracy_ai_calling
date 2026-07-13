# Digital Democracy AI Calling

An AI-powered calling system for public grievance intake, complaint triage, and civic response workflows.

This project combines voice AI, retrieval-augmented generation, analytics, and service orchestration to automate inbound civic complaints and outbound follow-up calls. The system is designed to support structured complaint capture, faster resolution, and better visibility for administrators.

## What it does

* Accepts voice-based calls and processes them through speech-to-text
* Uses an AI layer to understand the complaint and generate responses
* Stores and retrieves relevant context with FAISS-based semantic search
* Supports downstream analytics for monitoring, tracking, and escalation
* Runs as a containerized stack with Docker Compose
* Includes a smoke test script for end-to-end validation

## Project structure

The repository is organized around these core components:

* `backend/` — main API and application logic
* `rag-engine/` — retrieval and context handling
* `ai-services/` — AI-related service modules
* `analytics/` — reporting and monitoring utilities
* `database/` — persistence and storage-related assets
* `docker/` — container and deployment support
* `.env.example` — required environment variables
* `smoke_test.sh` — quick end-to-end health and call-flow test
* `makefile` — shortcuts for running and stopping the stack

## Tech stack

* Python
* FastAPI / Uvicorn
* Docker / Docker Compose
* Redis
* FAISS
* Speech-to-text service
* Text-to-speech service
* LLM service

## Environment variables

Create a `.env` file based on `.env.example`.

```env
REDIS_HOST=redis
FAISS_PATH=/data/faiss
LLM_API=http://llm:9000
STT_API=http://whisper:9000
TTS_API=http://tts:9000
```

## Getting started

### 1) Clone the repository

```bash
git clone https://github.com/spacebeige/digital_democracy_ai_calling.git
cd digital_democracy_ai_calling
```

### 2) Configure environment variables

Copy the example file and edit values as needed:

```bash
cp .env.example .env
```

### 3) Run the stack

Using Docker Compose:

```bash
docker compose up
```

Or using the Makefile:

```bash
make run
```

### 4) Stop the stack

```bash
docker compose down
```

Or:

```bash
make stop
```

### 5) Run the backend directly

If you want to run only the backend service locally:

```bash
uvicorn backend.app.main:app --reload
```

## Smoke test

The repository includes a shell script for validating the system end to end.

```bash
chmod +x smoke_test.sh
./smoke_test.sh /absolute/path/to/sample.wav
```

The script will:

1. Check backend health
2. Check downstream service health
3. Send an audio file through the call-handling pipeline

If your backend runs on a different host or port, set:

```bash
export BACKEND_URL=http://localhost:8000
```

## Typical flow

1. A call or audio input is received
2. Speech is transcribed into text
3. The complaint is analyzed and classified
4. Relevant context is retrieved from the knowledge store
5. The LLM generates the response or next action
6. The result is stored for analytics, tracking, or escalation

## Use cases

* Public grievance redressal
* Civic helpdesk automation
* Complaint intake and classification
* Outbound follow-up and status updates
* SLA tracking and escalation support
* AI-assisted call center workflows

## Why this project matters

Most grievance systems fail because they are too manual, too slow, or too hard for citizens to use. Voice-first AI solves that by making intake easier and response handling faster. The real value is not just answering calls — it is turning unstructured complaints into structured, trackable actions.

## Contributing

Contributions are welcome. Good starting points include:

* Improving the README and documentation
* Adding backend tests
* Strengthening Docker setup
* Expanding analytics dashboards
* Improving call-flow reliability
* Adding better error handling and logging
* Refining RAG retrieval quality

Before contributing, open an issue or describe the change clearly in your pull request.

## License

Add a license file if one is not already present. If the project is intended to be open source, use a license that matches how you want others to reuse the code.

## Acknowledgments

Built for civic AI workflows, grievance automation, and practical public-service use cases.
