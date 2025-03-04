from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import jwt
import bcrypt
import datetime
from typing import List
import openai
import studybud  # Importing Gen AI StudyBud

app = FastAPI()

# Database Setup
client = MongoClient("mongodb://localhost:27017")
db = client["ai_study_planner"]
users_collection = db["users"]
study_plans_collection = db["study_plans"]

# Secret Key for JWT
SECRET_KEY = "your_secret_key"
openai.api_key = "your_openai_api_key"

# User Model
class User(BaseModel):
    username: str
    password: str

# Study Plan Model
class StudyPlan(BaseModel):
    user_id: str
    subject: str
    topics: List[str]
    schedule: List[str]

# User Registration
@app.post("/register")
def register(user: User):
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="User already exists")
    
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    users_collection.insert_one({"username": user.username, "password": hashed_password})
    return {"message": "User registered successfully"}

# User Login
@app.post("/login")
def login(user: User):
    user_data = users_collection.find_one({"username": user.username})
    if not user_data or not bcrypt.checkpw(user.password.encode('utf-8'), user_data["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    token = jwt.encode({"username": user.username, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)}, SECRET_KEY, algorithm="HS256")
    return {"token": token}

# Generate AI-Powered Study Plan with StudyBud
@app.post("/generate-plan")
def generate_study_plan(user_id: str, subject: str):
    response = studybud.generate_study_plan(subject)  # Using StudyBud Gen AI
    topics = response.get("topics", [])
    schedule = response.get("schedule", [])
    
    plan = {"user_id": user_id, "subject": subject, "topics": topics, "schedule": schedule}
    study_plans_collection.insert_one(plan)
    return plan

# Get Study Plans for a User
@app.get("/plans/{user_id}")
def get_study_plans(user_id: str):
    plans = list(study_plans_collection.find({"user_id": user_id}, {"_id": 0}))
    return plans

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


