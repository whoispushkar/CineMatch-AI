
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p"

# Retry temporary connection failures and server errors.
retry_strategy = Retry(
    total=3,
    connect=3,
    read=3,
    status=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
    respect_retry_after_header=True,
)

session = requests.Session()
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)


def get_movie_details(movie_id):
    if not TMDB_API_KEY:
        print("TMDB error: TMDB_API_KEY is missing from .env")
        return None

    try:
        response = session.get(
            f"{BASE_URL}/movie/{int(movie_id)}",
            params={"api_key": TMDB_API_KEY},
            timeout=(10, 20),
            verify=True,
        )

        if response.status_code != 200:
            print(
                f"TMDB request failed for movie ID {movie_id}: "
                f"HTTP {response.status_code}"
            )
            return None

        return response.json()

    except (requests.RequestException, ValueError, TypeError) as exc:
        print(
            f"TMDB request failed after retries for movie ID "
            f"{movie_id}: {exc}"
        )
        return None


def get_poster(movie_id, size="w500"):
    movie = get_movie_details(movie_id)

    if not movie:
        return None

    poster_path = movie.get("poster_path")

    if not poster_path:
        print(f"No TMDB poster available for movie ID {movie_id}")
        return None

    return f"{IMAGE_BASE_URL}/{size}{poster_path}"


def get_backdrop(movie_id, size="w1280"):
    movie = get_movie_details(movie_id)

    if not movie:
        return None

    backdrop_path = movie.get("backdrop_path")

    if not backdrop_path:
        return None

    return f"{IMAGE_BASE_URL}/{size}{backdrop_path}"


def get_overview(movie_id):
    movie = get_movie_details(movie_id)
    return (movie or {}).get("overview") or ""


def get_genres(movie_id):
    movie = get_movie_details(movie_id)

    if not movie:
        return []

    return [
        genre["name"]
        for genre in movie.get("genres", [])
        if isinstance(genre, dict) and genre.get("name")
    ]
