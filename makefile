run:
    docker compose up

stop:
    docker compose down

backend:
    uvicorn backend.app.main:app --reload