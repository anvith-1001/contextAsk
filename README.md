# contextAsk Backend (Sanitized Version)
The site is regularly updated with new features that may not yet be committed to this repository. Visit the live site to experience the latest changes.
Last update: May 30, 2026.
Recent updates include temporary/private chat, tools and web search (to reduce hallucinations in normal mode), a more user-friendly UI/UX, improved markdown rendering, and many more features to come.

visit Site at: https://the-project-06-96706.web.app

A FastAPI backend for document-based retrieval augmented generation, chat management, authenticated user access, and image generation. The service uses MongoDB for application data and vector storage, Supabase for authentication, and Google/Voyage models for generation and embeddings.

The secrets are filtered.

## Features

- User authentication through Supabase bearer tokens
- Chat creation, listing, renaming, message retrieval, and deletion
- Document upload, parsing, chunking, embedding, and indexing
- Retrieval augmented question answering over indexed documents
- Image generation with per-user monthly usage limits
- Docker and Docker Compose support

## Tech Stack

- Python 3.12
- FastAPI
- Uvicorn
- MongoDB Atlas / PyMongo
- LangChain
- Supabase
- Google Generative AI

## Project Structure

```text
app/
  core/        Business logic, RAG pipeline, vector database, parsing, chat, and image generation
  models/      Pydantic request models
  routes/      FastAPI route definitions
  services/    Authentication service integration
  main.py      FastAPI application entry point
```

## Environment Variables

Create a local `.env` file from the example file:

```bash
cp .env.example .env
```

Configure the following values:

```text
MONGO_URI=
VOYAGE_API_KEY=
GOOGLE_API_KEY=
GOOGLE_IMAGE_MODEL=gemini-2.5-flash-image
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_KEY=
```

Do not commit `.env` or any real credentials. The repository includes `.env.example` only as a safe template.

## Local Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the API server (local):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

The API will be available at:

```text
http://localhost:8080
```

FastAPI documentation will be available at:

```text
http://localhost:8080/docs
```

## Docker

Build and run with Docker Compose:

```bash
docker compose up --build
```

The service will run on port `8080`.

## API Overview

Authentication is required for protected endpoints. Send a Supabase access token in the `Authorization` header:

```text
Authorization: Bearer <access_token>
```

Main route groups:

```text
/auth        User profile and account deletion
/chat        Chat creation, listing, updates, messages, and deletion
/documents   Document indexing
/ask         RAG question answering
/images      Image generation and image management
/chat( temp ) For Temporary chat
```

## Endpoints

```text
GET    /auth/me
DELETE /auth/delete-account

POST   /chat/create
GET    /chat/my-chats
GET    /chat/chat/{chat_id}/messages
PUT    /chat/update/{chat_id}
DELETE /chat/{chat_id}

POST   /documents/index

POST   /ask/ask

POST   /images/generate
GET    /images/
GET    /images/{image_id}
DELETE /images/{image_id}
```
