from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, decks, cards, analytics

# Create tables on startup. Fine for a project this size; a larger app
# would use Alembic migrations instead.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Flashcard Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(decks.router)
app.include_router(cards.router)
app.include_router(analytics.router)


@app.get("/health")
def health():
    return {"status": "ok"}
