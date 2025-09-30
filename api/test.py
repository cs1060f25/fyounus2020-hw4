from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
async def test():
    return {
        "status": "working",
        "current_dir": os.getcwd(),
        "files": os.listdir("."),
        "api_files": os.listdir("api") if os.path.exists("api") else "api dir not found"
    }

@app.post("/")
async def test_post():
    return {"status": "POST working"}
