# Digital Democracy AI Calling

An AI-powered calling system for public grievance intake, complaint triage, and civic response workflows.

This project combines voice AI, retrieval-augmented generation, analytics, and service orchestration to automate inbound civic complaints and outbound follow-up calls. The goal is simple: make it easier for citizens to register complaints and easier for administrators to process, track, and resolve them.

## Project Title & Description

**Digital Democracy AI Calling** is a voice-first civic automation system designed to handle public grievances through AI-assisted calling workflows.

It solves a common problem in public-service systems: complaints are often unstructured, slow to process, and hard to track. This project turns voice input into structured data, helps classify and respond to complaints, and supports follow-up, monitoring, and escalation.

## Features & Benefits

* **Voice-based complaint intake**
  Citizens can raise issues through audio or calls instead of filling long forms.

* **Speech-to-text processing**
  Incoming audio is converted into text for AI processing and record keeping.

* **AI-powered complaint understanding**
  The system can analyze the complaint and help generate a response or next action.

* **Retrieval-Augmented Generation (RAG)**
  Relevant context is fetched from a semantic store to improve the quality of responses.

* **FAISS-based search layer**
  Fast similarity search helps retrieve useful knowledge and prior context.

* **Analytics and monitoring support**
  Complaint flow can be tracked for status, escalation, and reporting.

* **Dockerized deployment**
  The stack is container-friendly and can be run through Docker Compose.

* **Smoke testing support**
  A built-in smoke test script helps validate the call flow end to end.

### Why this project is valuable

This project reduces manual effort, improves response speed, and makes grievance handling more structured. Instead of forcing citizens into rigid forms and slow processes, it uses voice and AI to make the system more accessible and operationally efficient.

## Tech Stack

* Python
* FastAPI / Uvicorn
* Docker / Docker Compose
* Redis
* FAISS
* Speech-to-Text service
* Text-to-Speech service
* LLM service

## Repository Structure

* `backend/` — main API and application logic
* `rag-engine/` — retrieval and context handling
* `ai-services/` — AI-related service modules
* `analytics/` — reporting and monitoring utilities
* `database/` — persistence and storage-related assets
* `docker/` — container and deployment support
* `.env.example` — required environment variables
* `smoke_test.sh` — end-to-end health and call-flow test
* `makefile` — shortcuts for running and stopping the stack

## Installation Instructions

### Prerequisites

Make sure you have the following installed:

* Docker
* Docker Compose
* Python 3.10+ recommended
* `uvicorn` if you want to run the backend directly

### Step 1: Clone the repository

```bash
git clone https://github.com/spacebeige/digital_democracy_ai_calling.git
cd digital_democracy_ai_calling
```

### Step 2: Create the environment file

Copy the example environment file and edit values if needed:

```bash
cp .env.example .env
```

### Step 3: Set environment variables

The project expects variables similar to these:

```env
REDIS_HOST=redis
FAISS_PATH=/data/faiss
LLM_API=http://llm:9000
STT_API=http://whisper:9000
TTS_API=http://tts:9000
```

### Step 4: Run the application

Using Docker Compose:

```bash
docker compose up
```

Or using the Makefile:

```bash
make run
```

### Step 5: Stop the application

Using Docker Compose:

```bash
docker compose down
```

Or:

```bash
make stop
```

### Step 6: Run the backend directly

If you want to run only the backend service locally:

```bash
uvicorn backend.app.main:app --reload
```

## Usage Examples

### Start the stack

```bash
docker compose up
```

### Run the backend locally

```bash
uvicorn backend.app.main:app --reload
```

### Run the smoke test

```bash
chmod +x smoke_test.sh
./smoke_test.sh /absolute/path/to/sample.wav
```

If your backend runs on a different host or port:

```bash
export BACKEND_URL=http://localhost:8000
```

## Typical Workflow

1. A call or audio input is received.
2. Speech is transcribed into text.
3. The complaint is analyzed and classified.
4. Relevant context is retrieved from the knowledge store.
5. The LLM generates a response or next action.
6. The result is stored for analytics, tracking, or escalation.

## Contribution Guidelines

Contributions are welcome.

Good contribution areas include:

* Improving documentation
* Adding backend tests
* Strengthening Docker setup
* Expanding analytics dashboards
* Improving call-flow reliability
* Adding better error handling and logging
* Refining retrieval quality in the RAG layer

### How to contribute

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Test your updates locally.
5. Open a pull request with a clear explanation.

### Recommended standards

* Keep code clean and readable.
* Use meaningful commit messages.
* Keep changes focused and small when possible.
* Document new behavior when needed.

## License Information

No license file was confirmed in the repository scan.

That means the project is **not clearly licensed yet**, so reuse rights are not fully defined. If you want this to be a true open-source project, add a license file. Common choices are:

* MIT License
* Apache 2.0
* GNU GPL v3

If no license is added, other people technically cannot assume broad reuse rights.

## Acknowledgments

Built for civic AI workflows, grievance automation, and practical public-service use cases.
