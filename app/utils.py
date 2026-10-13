# ============================================================
# utils.py
# Helper Functions
# ============================================================


import pandas as pd


# ============================================================
# Safe Float
# ============================================================

def safe_float(value, default=0.0):
    """
    Convert a value to float safely.
    """

    try:

        if pd.isna(value):
            return default

        return float(value)

    except Exception:
        return default


# ============================================================
# Safe Integer
# ============================================================

def safe_int(value, default=0):
    """
    Convert a value to integer safely.
    """

    try:

        if pd.isna(value):
            return default

        return int(value)

    except Exception:
        return default


# ============================================================
# Safe String
# ============================================================

def safe_string(value, default=""):

    """
    Convert value to string safely.
    """

    if pd.isna(value):
        return default

    return str(value)


# ============================================================
# Format Rating
# ============================================================

def format_rating(rating):

    rating = safe_float(rating)

    return round(rating, 2)


# ============================================================
# Format Similarity
# ============================================================

def format_similarity(score):

    score = safe_float(score)

    return round(score * 100, 2)


# ============================================================
# Release Year
# ============================================================

def get_release_year(date):

    """
    Returns only the release year.
    """

    if not date:
        return "Unknown"

    date = str(date)

    if len(date) >= 4:
        return date[:4]

    return "Unknown"


# ============================================================
# Runtime Formatting
# ============================================================

def format_runtime(runtime):

    runtime = safe_int(runtime)

    if runtime <= 0:
        return "Unknown"

    hours = runtime // 60

    minutes = runtime % 60

    return f"{hours}h {minutes}m"


# ============================================================
# Percentage
# ============================================================

def percentage(value):

    value = safe_float(value)

    return round(value * 100, 2)