from fastapi import FastAPI

from app.config.settings import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="Official-source chatbot for Purdue University Northwest information requests.",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "PNW Knowledge Chatbot API"}


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=(settings.environment == "development"))