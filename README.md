---
title: Customer Service AI
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
sdk_version: "latest"
app_file: main.py
pinned: false
---

# Customer Service AI Backend

FastAPI backend for Hadhramout Bank AI customer service system.

## Features
- Telegram webhook integration
- AI-powered responses using Groq
- Database integration with Supabase
- Vector search with Pinecone

## API Endpoints
- `GET /` - Health check
- `POST /webhook` - Telegram webhook endpoint
- `POST /test` - Test webhook functionality
- `GET /dns-test` - DNS connectivity test
- `GET /ai-test` - AI response test

## Deployment
This application is deployed on Hugging Face Spaces using Docker.

## Local Development
```bash
docker build -t customer-service .
docker run -p 8000:8000 customer-service
```
