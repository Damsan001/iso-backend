# CISO Backend

This repository contains the backend service for the CISO document management system. The service is built using FastAPI and provides endpoints for managing documents, versions, reviews, and responsible parties.

## Project Structure

project/
└── app/
├── main.py
├── routers/
│ └── documents.py
├── schemas/
│ ├── document.py
│ ├── responsible.py
│ ├── review.py
│ ├── version.py
│ └── export.py
├── services/
│ └── document_service.py
└── infrastructure/
└── document_repository.py
