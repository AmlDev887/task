from fastapi import FastAPI
from app.routers import auth, tasks
app = FastAPI(
    title = "Task Menejer API",
    description= "JIra"
)

app.include_router(auth.router)
app.include_router(tasks.router)

@app.get("/")
def root():
    return {"message": "Task Manager API is running"}