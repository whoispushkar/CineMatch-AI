
# ============================================================
# model_loader.py
# Loads, cleans, and prepares the movie recommendation model
# ============================================================

import ast
import re
import string
import warnings
from pathlib import Path

import nltk
import pandas as pd

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors


# ============================================================
# Project Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

MOVIES_PATH = DATA_DIR / "movies_metadata.csv"
CREDITS_PATH = DATA_DIR / "credits.csv"
KEYWORDS_PATH = DATA_DIR / "keywords.csv"


# ============================================================
# NLTK Resources
# ============================================================



def ensure_nltk_resource(resource_path, download_name):
    """Find an NLTK resource in extracted or ZIP form."""

    resource_paths = [resource_path]

    if resource_path.startswith("corpora/"):
        resource_paths.append(resource_path + ".zip")

    # Check whether the resource is already installed.
    for path in resource_paths:
        try:
            nltk.data.find(path)
            return
        except LookupError:
            continue

    # Download only if neither form is available.
    nltk_data_dir = Path.home() / "nltk_data"
    nltk_data_dir.mkdir(parents=True, exist_ok=True)

    success = nltk.download(
        download_name,
        download_dir=str(nltk_data_dir),
        quiet=True,
    )

    if not success:
        raise RuntimeError(
            f"Could not download NLTK resource: {download_name}"
        )

    # Check again after downloading.
    for path in resource_paths:
        try:
            nltk.data.find(path)
            return
        except LookupError:
            continue

    raise RuntimeError(
        f"NLTK resource is still unavailable: {download_name}"
    )


ensure_nltk_resource("corpora/stopwords", "stopwords")
ensure_nltk_resource("corpora/wordnet", "wordnet")
ensure_nltk_resource("corpora/omw-1.4", "omw-1.4")

STOP_WORDS = set(stopwords.words("english"))
LEMMATIZER = WordNetLemmatizer()


# ============================================================
# Data Validation Helpers
# ============================================================

def read_csv_safely(file_path):
    """Read a CSV file and report a useful error if it fails."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required dataset not found: {file_path}\n"
            "Make sure the CSV file exists in your project's data folder."
        )

    try:
        return pd.read_csv(file_path, low_memory=True)
    except Exception as exc:
        raise RuntimeError(
            f"Could not read dataset: {file_path.name}. "
            f"Details: {exc}"
        ) from exc


def validate_columns(dataframe, required_columns, filename):
    """Ensure a dataset contains the columns needed by the model."""

    missing = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing:
        raise ValueError(
            f"{filename} is missing required columns: {missing}"
        )


def parse_list(value):
    """
    Safely parse columns containing Python-list-like strings.

    Invalid, missing, or unexpected values return an empty list.
    """

    if isinstance(value, list):
        return value

    if not isinstance(value, str) or not value.strip():
        return []

    try:
        parsed = ast.literal_eval(value)
    except (ValueError, SyntaxError, TypeError):
        return []

    return parsed if isinstance(parsed, list) else []


def extract_names(value):
    """Extract names from genre or keyword data."""

    names = []

    for item in parse_list(value):
        if isinstance(item, dict):
            name = item.get("name")

            if name:
                names.append(str(name))

    return " ".join(names)


def extract_cast(value):
    """Return the first three available cast members."""

    actors = []

    for actor in parse_list(value)[:3]:
        if isinstance(actor, dict):
            name = actor.get("name")

            if name:
                actors.append(str(name).replace(" ", ""))

    return " ".join(actors)


def extract_director(value):
    """Return the director's name when available."""

    for member in parse_list(value):
        if not isinstance(member, dict):
            continue

        if member.get("job") == "Director":
            name = member.get("name")

            if name:
                return str(name).replace(" ", "")

    return ""


# ============================================================
# Text Cleaning
# ============================================================

def clean_text(text):
    """Normalize text before TF-IDF vectorization."""

    if pd.isna(text):
        return ""

    text = str(text).lower()

    text = text.translate(
        str.maketrans("", "", string.punctuation)
    )

    text = re.sub(r"\d+", "", text)
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    words = [
        LEMMATIZER.lemmatize(word)
        for word in text.split()
        if word not in STOP_WORDS
    ]

    return " ".join(words)


# ============================================================
# Load and Prepare Model
# ============================================================

def load_model():

    print("=" * 60)
    print("Loading Movie Recommendation Model...")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Load datasets
    # --------------------------------------------------------

    movies = read_csv_safely(MOVIES_PATH)
    credits = read_csv_safely(CREDITS_PATH)
    keywords = read_csv_safely(KEYWORDS_PATH)

    validate_columns(
        movies,
        [
            "id", "title", "overview", "genres", "tagline",
            "vote_average", "vote_count", "popularity",
            "release_date", "runtime",
        ],
        MOVIES_PATH.name,
    )

    validate_columns(
        credits,
        ["id", "cast", "crew"],
        CREDITS_PATH.name,
    )

    validate_columns(
        keywords,
        ["id", "keywords"],
        KEYWORDS_PATH.name,
    )

    print("Datasets loaded and validated.")

    # --------------------------------------------------------
    # 2. Clean movie IDs
    # --------------------------------------------------------

    for dataframe in (movies, credits, keywords):
        dataframe["id"] = pd.to_numeric(
            dataframe["id"],
            errors="coerce",
        )

        dataframe.dropna(subset=["id"], inplace=True)

        dataframe["id"] = dataframe["id"].astype("int64")

        dataframe.drop_duplicates(
            subset=["id"],
            keep="first",
            inplace=True,
        )

    # --------------------------------------------------------
    # 3. Merge datasets
    # --------------------------------------------------------

    movies = movies.merge(
        credits[["id", "cast", "crew"]],
        on="id",
        how="inner",
        validate="one_to_one",
    )

    movies = movies.merge(
        keywords[["id", "keywords"]],
        on="id",
        how="inner",
        validate="one_to_one",
    )

    print(f"Merged dataset contains {len(movies):,} movies.")

    if movies.empty:
        raise ValueError(
            "No movies remain after merging the datasets. "
            "Check whether the IDs match across all three CSV files."
        )

    # --------------------------------------------------------
    # 4. Select columns and handle missing values
    # --------------------------------------------------------

    required_columns = [
        "id",
        "title",
        "overview",
        "genres",
        "keywords",
        "cast",
        "crew",
        "tagline",
        "vote_average",
        "vote_count",
        "popularity",
        "release_date",
        "runtime",
    ]

    movies = movies[required_columns].copy()

    movies["title"] = movies["title"].fillna("").astype(str).str.strip()

    movies = movies[movies["title"] != ""].copy()

    movies.drop_duplicates(subset=["id"], keep="first", inplace=True)

    if movies.empty:
        raise ValueError(
            "No movies with valid titles were found in the datasets."
        )

    for column in ["overview", "tagline"]:
        movies[column] = movies[column].fillna("").astype(str)

    # --------------------------------------------------------
    # 5. Extract genres, keywords, cast, and director
    # --------------------------------------------------------

    print("Processing movie features...")

    movies["genres"] = movies["genres"].apply(extract_names)
    movies["keywords"] = movies["keywords"].apply(extract_names)
    movies["cast"] = movies["cast"].apply(extract_cast)
    movies["crew"] = movies["crew"].apply(extract_director)

    # --------------------------------------------------------
    # 6. Combine movie features into tags
    # --------------------------------------------------------

    movies["tag"] = (
        movies["overview"] + " "
        + movies["genres"] + " "
        + movies["keywords"] + " "
        + movies["cast"] + " "
        + movies["crew"] + " "
        + movies["tagline"]
    )

    # --------------------------------------------------------
    # 7. Build the final recommendation dataframe
    # --------------------------------------------------------

    final_df = movies[
        [
            "id",
            "title",
            "tag",
            "vote_average",
            "vote_count",
            "popularity",
            "release_date",
            "runtime",
        ]
    ].copy()

    numeric_columns = [
        "vote_average",
        "vote_count",
        "popularity",
        "runtime",
    ]

    for column in numeric_columns:
        final_df[column] = pd.to_numeric(
            final_df[column],
            errors="coerce",
        )

    final_df["vote_average"] = final_df["vote_average"].fillna(0.0)
    final_df["vote_count"] = final_df["vote_count"].fillna(0)
    final_df["popularity"] = final_df["popularity"].fillna(0.0)

    # --------------------------------------------------------
    # 8. Clean tags
    # --------------------------------------------------------

    print("Cleaning movie tags...")

    final_df["tag"] = final_df["tag"].apply(clean_text)

    # Remove movies that have no usable descriptive text.
    final_df = final_df[
        final_df["tag"].str.strip().ne("")
    ].copy()

    final_df.reset_index(drop=True, inplace=True)

    if final_df.empty:
        raise ValueError(
            "No movies have usable tags. Check your dataset contents."
        )

    print(f"Prepared {len(final_df):,} movies for recommendations.")

    # --------------------------------------------------------
    # 9. Create TF-IDF feature matrix
    # --------------------------------------------------------

    print("Creating TF-IDF feature matrix...")

    vectorizer_options = {
        "max_features": 3000,
        "stop_words": "english",
        "ngram_range": (1, 2),
        "sublinear_tf": True,
        "dtype": float,
    }

    try:
        tfidf = TfidfVectorizer(
            min_df=2,
            max_df=0.8,
            **vectorizer_options,
        )

        tfidf_matrix = tfidf.fit_transform(final_df["tag"])

    except ValueError as exc:
        # Small datasets may not satisfy min_df=2 or max_df=0.8.
        if "empty vocabulary" not in str(exc).lower() and (
            "no terms remain" not in str(exc).lower()
        ):
            raise

        print(
            "Using relaxed TF-IDF frequency limits "
            "because the dataset is small or sparse."
        )

        tfidf = TfidfVectorizer(
            min_df=1,
            max_df=1.0,
            **vectorizer_options,
        )

        tfidf_matrix = tfidf.fit_transform(final_df["tag"])

    print(
        f"TF-IDF matrix created: "
        f"{tfidf_matrix.shape[0]:,} movies, "
        f"{tfidf_matrix.shape[1]:,} features."
    )

    # --------------------------------------------------------
    # 10. Train nearest-neighbor model
    # --------------------------------------------------------

    neighbor_count = min(11, len(final_df))

    print("Training Nearest Neighbors...")

    nn_model = NearestNeighbors(
        n_neighbors=neighbor_count,
        metric="cosine",
        algorithm="brute",
        n_jobs=-1,
    )

    nn_model.fit(tfidf_matrix)

    print("Nearest Neighbor model trained.")

    # --------------------------------------------------------
    # 11. Create title lookup index
    # --------------------------------------------------------

    final_df["title_lower"] = (
        final_df["title"].str.strip().str.lower()
    )

    indices = pd.Series(
        final_df.index,
        index=final_df["title_lower"],
    )

    indices = indices[
        ~indices.index.duplicated(keep="first")
    ]

    print("Movie title index created.")

    # --------------------------------------------------------
    # 12. Calculate weighted-rating parameters
    # --------------------------------------------------------

    valid_ratings = final_df.loc[
        final_df["vote_average"] > 0,
        "vote_average",
    ]

    C = float(valid_ratings.mean()) if not valid_ratings.empty else 0.0

    m = float(final_df["vote_count"].quantile(0.70))

    # --------------------------------------------------------
    # 13. Return model objects
    # --------------------------------------------------------

    print("=" * 60)
    print("Movie recommendation model loaded successfully!")
    print("=" * 60)

    return {
        "movies": movies,
        "final_df": final_df,
        "tfidf": tfidf,
        "tfidf_matrix": tfidf_matrix,
        "nn_model": nn_model,
        "indices": indices,
        "C": C,
        "m": m,
    }


# ============================================================
# Load Model and Expose Existing Variables
# ============================================================

model = load_model()

movies = model["movies"]
final_df = model["final_df"]
tfidf = model["tfidf"]
tfidf_matrix = model["tfidf_matrix"]
nn_model = model["nn_model"]
indices = model["indices"]
C = model["C"]
m = model["m"]
