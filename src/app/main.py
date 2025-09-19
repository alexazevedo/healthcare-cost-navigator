from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.endpoints import router
from .core.config import settings
from .core.logging import setup_logging

# Initialize logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/openapi.json",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Healthcare Cost Navigator API"}
