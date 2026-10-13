# ============================================================
# recommender.py
# Movie Recommendation Functions
# ============================================================

from difflib import get_close_matches

from app.model_loader import (
    final_df,
    tfidf_matrix,
    nn_model,
    indices,
    C,
    m,
)

# ============================================================
# Search Movie
# ============================================================

def search_movie(movie_name):
    """
    Returns the closest movie title if an exact match
    is not found.
    """

    if movie_name is None:
        return None

    movie_name = str(movie_name).strip()

    if movie_name == "":
        return None

    movie_name = movie_name.lower()

    # Exact match
    if movie_name in indices:
        return movie_name

    # Fuzzy match
    matches = get_close_matches(
        movie_name,
        indices.index.tolist(),
        n=1,
        cutoff=0.6,
    )

    if matches:
        return matches[0]

    return None


# ============================================================
# Recommend Movies
# ============================================================

def recommend(movie_name, n_recommendations=10):

    print("=" * 60)
    print("recommend() called")
    print("Movie requested:", movie_name)

    # --------------------------------------------------------
    # Search Movie
    # --------------------------------------------------------

    movie_name = search_movie(movie_name)

    if movie_name is None:
        print("Movie not found.")
        return {
            "success": False,
            "message": "Movie not found!",
            "recommendations": []
        }

    print("Movie found:", movie_name)

    # --------------------------------------------------------
    # Movie Index
    # --------------------------------------------------------

    movie_idx = indices[movie_name]

    print("Movie index:", movie_idx)

    # --------------------------------------------------------
    # Find Nearest Neighbours
    # --------------------------------------------------------

    print("Calculating nearest neighbours...")

    distances, neighbour_indices = nn_model.kneighbors(
        tfidf_matrix[movie_idx],
        n_neighbors=n_recommendations + 1
    )

    print("Nearest neighbours calculated.")

    distances = distances.flatten()[1:]
    neighbour_indices = neighbour_indices.flatten()[1:]

    similarity = 1 - distances

    # --------------------------------------------------------
    # Movie Details
    # --------------------------------------------------------

    print("Preparing recommendation dataframe...")

    recommendations = final_df.iloc[
        neighbour_indices
    ][
        [
            "id",
            "title",
            "vote_average",
            "vote_count",
            "popularity",
            "release_date",
        ]
    ].copy()

    recommendations["similarity"] = similarity

    # --------------------------------------------------------
    # IMDb Weighted Rating
    # --------------------------------------------------------

    recommendations["weighted_rating"] = (
        (
            recommendations["vote_count"]
            /
            (
                recommendations["vote_count"] + m
            )
        )
        *
        recommendations["vote_average"]
    ) + (
        (
            m
            /
            (
                recommendations["vote_count"] + m
            )
        )
        *
        C
    )

    # --------------------------------------------------------
    # Rating Score
    # --------------------------------------------------------

    recommendations["rating_score"] = (
        recommendations["weighted_rating"]
        /
        recommendations["weighted_rating"].max()
    )

    # --------------------------------------------------------
    # Popularity Score
    # --------------------------------------------------------

    recommendations["popularity_score"] = (
        recommendations["popularity"]
        /
        recommendations["popularity"].max()
    )

    # --------------------------------------------------------
    # Final Score
    # --------------------------------------------------------

    recommendations["final_score"] = (
        0.85
        * recommendations["similarity"]
        +
        0.10
        * recommendations["rating_score"]
        +
        0.05
        * recommendations["popularity_score"]
    )

    recommendations = recommendations.sort_values(
        by="final_score",
        ascending=False,
    )

    recommendations = recommendations.reset_index(drop=True)

    print("Recommendations prepared.")
    print("Returning response...")
    print("=" * 60)

    return {
        "success": True,
        "searched_movie": final_df.iloc[movie_idx]["title"],
        "recommendations": recommendations[
            [
                "id",
                "title",
                "similarity",
                "weighted_rating",
                "vote_average",
                "vote_count",
                "popularity",
                "release_date",
                "final_score",
            ]
        ].to_dict(orient="records")
    }