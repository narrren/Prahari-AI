# PRAHARI-AI: Execution Guide

## Prerequisites
- Docker & Docker Compose
- Python 3.9+
- Node.js 16+

## 1. Start Infrastructure
Spin up LocalStack (AWS Simulator) and Ganache (Blockchain Simulator).
```bash
docker-compose up -d
```

## 2. Initialize Database for LocalStack
Create the DynamoDB tables.
```bash
# Activate virtual env if not active
.\venv\Scripts\Activate
python backend/database/setup_dynamodb.py
```

## 3. Start Backend API
Runs the FastAPI microservice on port 8000.
```bash
# In the root directory
uvicorn backend.app.main:app --reload
```
Check API Docs: http://localhost:8000/api/v1/docs

## 4. Start Dashboard
Runs the Command Centre UI on port 5173.
```bash
cd frontend/dashboard
npm run dev
```
Open Browser: http://localhost:5173

## 5. run Simulation
Generate and replay tourist telemetry data to see the dashboard light up.
```bash
# Open a new terminal
python scripts/generate_trek_data.py
python scripts/replay_trek.py
```

## Architecture Notes
- **Backend**: Clean Architecture (FastAPI, Service Layer, Pydantic Models).
- **Security**: CORS, Input Validation, Role-Based Access Control logic in Smart Contracts.
- **Frontend**: Real-time polling, Alert System, Dark Mode Aesthetics.
