from fastapi import FastAPI
from cleaningFile import clean_chat_data
from relationCalculator import calculate_relationships
from jsonConverter import generate_timelines
from analyzer import run_analysis

app = FastAPI()

@app.post("/clean")
async def clean():
    result = clean_chat_data()
    return {"success": True, "data": result}

@app.post("/score")
async def score():
    result = calculate_relationships()
    return {"success": True, "data": result}

@app.post("/timeline")
async def timeline():
    result = generate_timelines()
    return {"success": True, "data": result}

@app.post("/analyze")
async def analyze():
    result = run_analysis()
    return {"success": True, "data": result}