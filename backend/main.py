import os
from dotenv import load_dotenv
import requests
import psycopg2
import time
import random
import threading
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import numpy as np
import asyncio
import csv
import io

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Added CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# ==============================
# DATABASE CONNECTION
# ==============================


def get_connection():
    """
    Get database connection using environment variables.
    Falls back to local development settings if env vars not set.
    """
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
        database=os.environ.get("DB_NAME", "defaultdb"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgres"),
        sslmode=os.environ.get("DB_SSLMODE", "prefer")  # Use "require" for Aiven
    )


# ==============================
# CREATE TABLES
# ==============================
def create_tables():

    conn = get_connection()
    cur = conn.cursor()

    # Sensor data table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sensor_data (
        id SERIAL PRIMARY KEY,
        node_id VARCHAR(50),
        field1 FLOAT,
        field2 FLOAT,
        created_at TIMESTAMP
    )
    """)

    # Tank parameters table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tank_sensorparameters (
        id SERIAL PRIMARY KEY,
        node_id VARCHAR(50),
        tank_height_cm FLOAT,
        tank_length_cm FLOAT,
        tank_width_cm FLOAT,
        lat FLOAT,
        long FLOAT
    )
    """)

    # Predictions history table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id SERIAL PRIMARY KEY,
        node_id VARCHAR(50),
        distance FLOAT,
        temperature FLOAT,
        prediction VARCHAR(50),
        confidence FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


# ==============================
# THINGSPEAK CONFIG
# ==============================
REAL_DATA_WITH_CURRENT_TIME = False
TEST_MODE = True

# Node id of sensor
NODE_ID = "NODE_001"

# ThingSpeak API
url = "https://api.thingspeak.com/channels/3290444/feeds.json?api_key=AWP8F08WA7SLO5EQ&results=-1"

last_created_at = None


# ==============================
# GENERATE TEST DATA
# ==============================
def generate_test_data():

    base_values = {
        "distance": 94.0,
        "temperature": 20.8
    }

    return {
        "distance": round(base_values["distance"] + random.uniform(-10, 10), 1),
        "temperature": round(base_values["temperature"] + random.uniform(-2, 2), 1),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# ==============================
# EMAIL ALERTS
# ==============================
def send_anomaly_email(distance, temperature):
    """
    Sends an email alert when an anomaly is detected (e.g., highly unusual distance or temp).
    """
    sender_email = os.environ.get("SMTP_EMAIL", "system@hitamiot.com")
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@hitamiot.com")
    
    print(f"⚠️ ANOMALY DETECTED: Dist {distance}cm, Temp {temperature}°C")
    print(f"📧 Sending Mock Email Alert to {admin_email} from {sender_email}...")
    print(f"    Subject: CRITICAL: Water System Anomaly Detected")
    print(f"    Body: Immediate attention required. Abnormal sensor readings logged.")

# ==============================
# WEBSOCKET MANAGER
# ==============================
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/sensor-data")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ==============================
# SENSOR DATA COLLECTOR
# ==============================
async def sensor_collector_async():

    print("Distance & Temperature Async Data Collector Started")

    while True:
        try:
            if TEST_MODE:
                test_data = generate_test_data()
                distance = test_data["distance"]
                temperature = test_data["temperature"]
                created_at = test_data["created_at"]
            else:
                response = requests.get(url)
                data = response.json()
                feed = data["feeds"][0]
                distance = float(feed["field1"])
                temperature = float(feed["field2"])
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print("NEW DATA:", distance, temperature, created_at)

            # Check for anomalies to send email
            if distance > 100 or temperature > 35 or temperature < 5:
                send_anomaly_email(distance, temperature)

            # Insert into DB
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO sensor_data
            (node_id, field1, field2, created_at)
            VALUES (%s,%s,%s,%s)
            """, (NODE_ID, distance, temperature, created_at))
            conn.commit()
            cur.close()
            conn.close()

            # Predict current activity for websocket broadcast
            if ml_model is not None:
                pred_label, conf = ml_predict(distance, temperature, [0.0]*5)
            else:
                pred_label, conf = mock_predict(distance, temperature)

            # Broadcast new data
            await manager.broadcast({
                "type": "new_sensor_data",
                "distance": distance,
                "temperature": temperature,
                "prediction": pred_label,
                "confidence": conf,
                "created_at": created_at
            })

            print("Sensor data inserted and broadcasted")
        except Exception as e:
            print("Collector Error:", e)

        await asyncio.sleep(20)


# ==============================
# REQUEST MODEL
# ==============================
class TankParameters(BaseModel):

    node_id: str
    tank_height_cm: float
    tank_length_cm: float
    tank_width_cm: float
    lat: float
    long: float

class PredictionRequest(BaseModel):

    distance: float
    temperature: float
    time_features: list[float]


# ==============================
# POST API
# ==============================
@app.post("/tank-parameters")
def create_tank_parameters(data: TankParameters):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO tank_sensorparameters
    (node_id, tank_height_cm, tank_length_cm, tank_width_cm, lat, long)
    VALUES (%s,%s,%s,%s,%s,%s)
    RETURNING id
    """,
                (
                    data.node_id,
                    data.tank_height_cm,
                    data.tank_length_cm,
                    data.tank_width_cm,
                    data.lat,
                    data.long
                ))

    new_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "Tank parameters inserted successfully",
        "id": new_id
    }


# ==============================
# GET API
# ==============================
@app.get("/tank-parameters")
def get_tank_parameters():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM tank_sensorparameters")

    rows = cur.fetchall()

    cur.close()
    conn.close()

    result = []

    for row in rows:
        result.append({
            "id": row[0],
            "node_id": row[1],
            "tank_height_cm": row[2],
            "tank_length_cm": row[3],
            "tank_width_cm": row[4],
            "lat": row[5],
            "long": row[6]
        })

    return result


# ==============================
# GET SENSOR DATA API
# ==============================

@app.get("/sensor-data")
def get_sensor_data(node_id: str = None):

    conn = get_connection()
    cur = conn.cursor()

    if node_id:
        cur.execute("""
        SELECT id,node_id,field1,field2,created_at
        FROM sensor_data
        WHERE node_id = %s
        ORDER BY created_at DESC
        """, (node_id,))
    else:
        cur.execute("""
        SELECT id,node_id,field1,field2,created_at
        FROM sensor_data
        ORDER BY created_at DESC
        """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    result = []

    for row in rows:
        result.append({
            "id": row[0],
            "node_id": row[1],
            "distance": row[2],
            "temperature": row[3],
            "created_at": row[4]
        })

    return result


# ==============================
# ML MODEL LOADING
# ==============================
ml_model = None
MODEL_PATH = os.path.join(os.path.dirname(__file__), "saved_models", "best_model.h5")

def load_ml_model():
    """Attempt to load the ML model. Falls back to mock predictions if unavailable."""
    global ml_model
    try:
        from tensorflow.keras.models import load_model
        if os.path.exists(MODEL_PATH):
            ml_model = load_model(MODEL_PATH)
            print(f"ML model loaded successfully from {MODEL_PATH}")
        else:
            print(f"Model file not found at {MODEL_PATH}. Using mock predictions.")
    except ImportError:
        print("TensorFlow not available. Using mock predictions.")
    except Exception as e:
        print(f"Error loading model: {e}. Using mock predictions.")


def mock_predict(distance, temperature):
    """Mock prediction based on sensor value ranges when ML model is unavailable."""
    classes = ["filling", "flush", "geyser", "no_activity", "washing_machine"]
    
    if distance < 30:
        prediction_label = "no_activity"
        confidence = 0.92
    elif distance < 50:
        prediction_label = random.choice(["shower", "faucet"])
        confidence = round(random.uniform(0.75, 0.95), 3)
    elif distance < 80:
        prediction_label = random.choice(["toilet", "dishwasher"])
        confidence = round(random.uniform(0.70, 0.90), 3)
    else:
        prediction_label = "no_activity"
        confidence = round(random.uniform(0.80, 0.95), 3)
    
    return prediction_label, confidence


def ml_predict(distance, temperature, time_features):
    """Run actual ML model prediction."""
    try:
        # Prepare input features (adjust shape based on your model's expected input)
        features = [distance, temperature] + time_features
        input_data = np.array(features).reshape(1, len(features), 1)
        
        prediction = ml_model.predict(input_data, verbose=0)
        classes = ["filling", "flush", "geyser", "no_activity", "washing_machine"]
        
        predicted_index = int(np.argmax(prediction[0]))
        confidence = float(np.max(prediction[0]))
        prediction_label = classes[predicted_index]
        
        return prediction_label, round(confidence, 3)
    except Exception as e:
        print(f"ML prediction failed: {e}. Falling back to mock.")
        return mock_predict(distance, temperature)


# ==============================
# PREDICTION API
# ==============================
@app.post("/api/v1/predict")
async def predict_water_activity(data: PredictionRequest):
    """
    Predict water activity based on sensor data.
    Uses ML model if available, otherwise falls back to mock predictions.
    Input: {"distance": float, "temperature": float, "time_features": list}
    Output: {"prediction": string, "confidence": float}
    """
    # Use ML model if loaded, otherwise mock
    if ml_model is not None:
        prediction_label, confidence = ml_predict(
            data.distance, data.temperature, data.time_features
        )
        prediction_source = "ml_model"
    else:
        prediction_label, confidence = mock_predict(data.distance, data.temperature)
        prediction_source = "mock"
    
    # Store prediction in database
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO predictions (node_id, distance, temperature, prediction, confidence)
        VALUES (%s, %s, %s, %s, %s)
        """, ("NODE_001", data.distance, data.temperature, prediction_label, confidence))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error storing prediction: {e}")
    
    return {
        "prediction": prediction_label,
        "confidence": confidence,
        "source": prediction_source
    }


class AuthRequest(BaseModel):
    username: str
    password: str

# In a real app, use hashed passwords and a 'users' table.
MOCK_USERS = {
    "admin": "admin123",
    "testuser": "password"
}

@app.post("/api/v1/auth/register")
async def register(data: AuthRequest):
    if data.username in MOCK_USERS:
        raise HTTPException(status_code=400, detail="Username already exists")
    MOCK_USERS[data.username] = data.password
    return {"message": "User registered successfully"}

@app.post("/api/v1/auth/login")
async def login(data: AuthRequest):
    if data.username not in MOCK_USERS or MOCK_USERS[data.username] != data.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    # Return a mock JWT token
    return {"access_token": f"mock_jwt_token_for_{data.username}", "token_type": "bearer"}

# ==============================
# MODEL INFO API
# ==============================
@app.get("/api/v1/model-info")
async def get_model_info():
    """
    Return information about the deployed ML model
    """
    return {
        "model_type": "GRU",
        "version": "3.0",
        "accuracy": 0.9266,  # Updated with enhanced model accuracy
        "last_trained": "2026-03-18",
        "classes": ["filling", "flush", "geyser", "no_activity", "washing_machine"]
    }


# ==============================
# PREDICTIONS HISTORY API
# ==============================
@app.get("/api/v1/predictions-history")
async def get_predictions_history(limit: int = 100):
    """
    Get historical predictions with timestamps
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT id, node_id, distance, temperature, prediction, confidence, created_at
    FROM predictions
    ORDER BY created_at DESC
    LIMIT %s
    """, (limit,))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "node_id": row[1],
            "distance": row[2],
            "temperature": row[3],
            "prediction": row[4],
            "confidence": row[5],
            "created_at": row[6]
        })
    
    return result


# ==============================
# BATCH PREDICTION API (CSV)
# ==============================
@app.post("/api/v1/predict/batch")
async def batch_predict_csv(file: UploadFile = File(...)):
    """
    Accepts a CSV file with columns: distance, temperature, time_features...
    Returns a JSON list of predictions.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    content = await file.read()
    try:
        decoded = content.decode('utf-8')
    except Exception:
        raise HTTPException(status_code=400, detail="Error decoding file string.")
    
    csv_reader = csv.DictReader(io.StringIO(decoded))
    results = []
    
    for row in csv_reader:
        try:
            distance = float(row.get('distance', 0))
            temperature = float(row.get('temperature', 0))
            # Extract time features if they exist (assuming column names like time_0, time_1)
            time_features = []
            for k in row.keys():
                if k.startswith('time_'):
                    time_features.append(float(row[k]))
            
            if len(time_features) == 0:
                time_features = [0.0] * 5 # dummy time features if none provided
                
            if ml_model is not None:
                pred_label, conf = ml_predict(distance, temperature, time_features)
            else:
                pred_label, conf = mock_predict(distance, temperature)
                
            results.append({
                "distance": distance,
                "temperature": temperature,
                "prediction": pred_label,
                "confidence": conf
            })
        except Exception as e:
            # Skip malformed rows
            continue
            
    return {"status": "success", "total_processed": len(results), "results": results}


# ==============================
# START BACKGROUND COLLECTOR
# ==============================
@app.on_event("startup")
async def start_background_tasks():

    create_tables()
    load_ml_model()  # Attempt to load ML model at startup

    asyncio.create_task(sensor_collector_async())


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
