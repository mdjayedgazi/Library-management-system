from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import admin, auth, books
from app.core.database import create_db_and_tables, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()

    yield

    await engine.dispose()


app = FastAPI(
    lifespan=lifespan,
)

# Allow the local Vite/React dev server to call the API from the browser.
# Only localhost origins are allowed; production origins should be added
# explicitly when a deployment origin is known.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(admin.router)
