# 🚀 Deployment and Usage Guide

Production deployment with Docker and SSL certificate setup.

## Quick Deployment

### Prerequisites

- AWS EC2 instance (Linux)
- Docker and Docker Compose installed
- Port 8001 open in security groups

### Deploy

```bash
cd resources
./deploy.sh
```

**Stack**: Django + Nginx + Elasticsearch + Ollama on `https://54.219.76.120:8001/`

## 🔒 SSL Certificate Setup (Required)

**⚠️ First-time users must accept the self-signed SSL certificate:**

1. **Navigate to**: `https://54.219.76.120:8001/`
2. **Accept the security warning**:
   - **Chrome**: "Advanced" → "Proceed to 54.219.76.120 (unsafe)"
   - **Firefox**: "Advanced" → "Accept the Risk and Continue"  
   - **Safari**: "Show Details" → "visit this website" → "Visit Website"
   - **Edge**: "Advanced" → "Continue to 54.219.76.120 (unsafe)"
3. **Done** - API will now work in your browser

## API Endpoints

Base URL: `https://54.219.76.120:8001/`

### 1. Maintenance Assistant

```http
POST /api/maintenance/process-document/
```

Extract maintenance schedules and task plans from documents.

### 2. Service Manuals Assistant  

```http
POST /api/service-manuals/process-document/
```

Extract task plans and procedures from service manuals.

### 3. Safety Procedures Assistant

```http
POST /api/safety-procedures/process-incident-report/
```

Analyze safety documents for hazards and precautions.

### 4. Training Manuals Assistant

```http
POST /api/training-manuals/process-training-manual/
```

Extract technician qualifications and certification requirements.

### 5. Equipment Entry Generator

```http
POST /api/equipment-entries/generate/test/
```

Generate equipment entries based on validation rules.
