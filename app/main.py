# ============================================================
# main.py
# FastAPI Backend
# ============================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.recommender import recommend
from app.model_loader import final_df
from app.schemas import RecommendRequest

# ============================================================
# FastAPI App
# ============================================================

app = FastAPI(
    title="Movie Recommendation API",
    description="Content-Based Movie Recommendation System",
    version="1.0.0"
)

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Change this after deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Home Route
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Movie Recommendation API is Running!",
        "status": "success"
    }


# ============================================================
# Health Check
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# Search Movies
# ============================================================

@app.get("/search")
def get_movies(query: str = ""):

    titles = final_df["title"].tolist()

    if query == "":
        return titles[:20]

    query = query.lower()

    filtered_movies = [
        movie
        for movie in titles
        if query in movie.lower()
    ]

    return filtered_movies[:20]


# ============================================================
# Recommend Movies
# ============================================================

@app.post("/recommend")
def recommend_movies(request: RecommendRequest):

    result = recommend(
        request.movie_name,
        request.n_recommendations,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result["message"]
        )

    return result