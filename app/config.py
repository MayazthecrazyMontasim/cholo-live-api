"""
Configuration for Cholo backend
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./cholo.db"  # Default: SQLite for dev, use PostgreSQL for production
)

# API
API_V1_STR = "/api/v1"
PROJECT_NAME = "Cholo Travel Planner"
PROJECT_VERSION = "1.0.0"

# CORS
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8000,https://cholo-frontend.vercel.app"
).split(",")

# Third-party APIs (stored server-side only — never exposed to frontend)
FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY", "")

# Stripe (for billing)
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

# Email (for invitations)
SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
