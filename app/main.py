from fastapi import FastAPI
from app.routers import auth, tasks, attachments, comments, health, projects, tags, users
app = FastAPI(
    title = "Task Menejer API",
    description= "JIra"
)

app.include_router(auth.router)
app.include_router(attachments.router)
app.include_router(comments.router)
app.include_router(health.router)
app.include_router(projects.router)
app.include_router(tags.router)
app.include_router(tasks.router)
app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "Task Manager API is running"}