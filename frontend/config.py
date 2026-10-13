
import os

FASTAPI_URL = os.getenv(
    "FASTAPI_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

RECOMMEND_ENDPOINT = f"{FASTAPI_URL}/recommend"
SEARCH_ENDPOINT = f"{FASTAPI_URL}/search"
