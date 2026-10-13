# ============================================================
# schemas.py
# Pydantic Models for FastAPI
# ============================================================

from pydantic import BaseModel, Field
from typing import List


# ============================================================
# Request Schema
# ============================================================

class RecommendRequest(BaseModel):
    movie_name: str = Field(
        ...,
        min_length=1,
        example="Interstellar",
        description="Movie name entered by the user"
    )

    n_recommendations: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Number of recommendations to return"
    )


# ============================================================
# Individual Movie Schema
# ============================================================

class MovieRecommendation(BaseModel):
    title: str

    similarity: float

    weighted_rating: float

    vote_average: float

    vote_count: float

    popularity: float

    release_date: str | None

    final_score: float


# ============================================================
# Response Schema
# ============================================================

class RecommendResponse(BaseModel):
    success: bool

    searched_movie: str | None = None

    message: str | None = None

    recommendations: List[MovieRecommendation]