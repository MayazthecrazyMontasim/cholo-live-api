from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth, destinations, budget, trips, chat

# Create DB Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Cholo Backend API",
    description="REST API for Cholo travel planner",
    version="1.0.0"
)

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(destinations.router)
app.include_router(budget.router)
app.include_router(trips.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Cholo API! Explore the API dynamically via /docs."}
