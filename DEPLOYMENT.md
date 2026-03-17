# Render Deployment Configuration

## Backend Deployment
- **Service Type**: Web Service
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Frontend Deployment
- **Service Type**: Static Site
- **Build Command**: `npm install && npm run build`
- **Publish Directory**: `build`

## Environment Variables (Backend)
Add these in Render dashboard (get values from Aiven):
- `DB_HOST`: [From Aiven dashboard]
- `DB_PORT`: [From Aiven dashboard]
- `DB_NAME`: [From Aiven dashboard]
- `DB_USER`: [From Aiven dashboard]
- `DB_PASSWORD`: [From Aiven dashboard - KEEP SECRET]
- `DB_SSLMODE`: require

## Frontend Environment Variables
- `REACT_APP_API_BASE_URL`: https://your-backend-service.onrender.com