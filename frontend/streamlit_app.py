"""CineMatch AI — polished Streamlit movie recommendation frontend."""

import html
from pathlib import Path

import requests
import streamlit as st

from config import RECOMMEND_ENDPOINT
from tmdb import get_movie_details, get_poster, IMAGE_BASE_URL


# -----------------------------------------------------------------------------
# Page setup and styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="CineMatch AI | Discover your next favourite",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --cm-bg: #0b0c10;
        --cm-panel: #14161d;
        --cm-panel-2: #1b1e28;
        --cm-border: rgba(255,255,255,.09);
        --cm-red: #f52235;
        --cm-muted: #a6a9b5;
        --cm-text: #f5f6fa;
    }
    .stApp {
        background: radial-gradient(ellipse at 50% -15%, #242034 0%, #101117 42%, var(--cm-bg) 75%);
        color: var(--cm-text);
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 1440px; padding-top: 1.5rem; padding-bottom: 2rem; }
    .cm-hero { padding: 2.2rem 1rem 1.7rem; text-align: center; }
    .cm-brand { font-size: clamp(2.2rem, 5vw, 3.6rem); line-height: 1.1; font-weight: 850; letter-spacing: -1.5px; }
    .cm-brand .accent { color: var(--cm-red); }
    .cm-tagline { margin-top: .8rem; color: #c2c4cf; font-size: 1.05rem; }
    .cm-eyebrow { color: #ff6875; text-transform: uppercase; letter-spacing: 2px; font-size: .72rem; font-weight: 800; }
    .cm-section-title { font-size: 1.45rem; font-weight: 800; margin: .3rem 0 .2rem; }
    .cm-section-subtitle { color: var(--cm-muted); margin-bottom: 1.2rem; }
    .cm-result-banner { background: linear-gradient(110deg, #211b32, #171b2b 70%, #1e1824); border: 1px solid var(--cm-border); border-radius: 18px; padding: 1.1rem 1.35rem; margin: 1.2rem 0 1.6rem; }
    .cm-result-label { color: #b5b8c6; font-size: .8rem; text-transform: uppercase; letter-spacing: 1.3px; }
    .cm-result-title { font-size: 1.45rem; font-weight: 800; margin-top: .15rem; }
    .cm-result-title span { color: var(--cm-red); }
    .cm-card-title { font-size: 1.03rem; font-weight: 800; line-height: 1.35; min-height: 2.7rem; margin: .7rem 0 .55rem; }
    .cm-meta { color: var(--cm-muted); font-size: .82rem; margin: .25rem 0; }
    .cm-score-wrap { margin-top: .9rem; padding: .75rem .8rem; background: #101219; border: 1px solid var(--cm-border); border-radius: 12px; }
    .cm-score-label { display: flex; justify-content: space-between; gap: .5rem; color: #c2c4cf; font-size: .78rem; margin-bottom: .45rem; }
    .cm-score-track { height: 6px; border-radius: 999px; background: #303340; overflow: hidden; }
    .cm-score-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #ff5362, var(--cm-red)); }
    .cm-footer { color: #858997; text-align: center; font-size: .82rem; padding: 1.5rem .5rem .3rem; }
    div[data-testid="stVerticalBlockBorderWrapper"] { background: rgba(20,22,29,.9); border-color: var(--cm-border) !important; border-radius: 16px !important; }
    div[data-testid="stImage"] img { border-radius: 10px; }
    div[data-testid="stTextInput"] input { background: #171922; border: 1px solid #353744; border-radius: 10px; min-height: 46px; }
    div[data-testid="stSlider"] [data-baseweb="slider"] { padding-top: .2rem; }
    .stButton > button[kind="primary"] { background: var(--cm-red); border: 1px solid var(--cm-red); border-radius: 10px; min-height: 46px; font-weight: 750; }
    .stButton > button[kind="primary"]:hover { background: #d91b2d; border-color: #d91b2d; }
    hr { border-color: var(--cm-border); }
    @media (max-width: 700px) {
        .cm-hero { padding-top: 1.2rem; }
        .cm-card-title { min-height: auto; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------
if "recommendations" not in st.session_state:
    st.session_state.recommendations = None
if "searched_movie" not in st.session_state:
    st.session_state.searched_movie = ""
if "selected_movie_id" not in st.session_state:
    st.session_state.selected_movie_id = None


# -----------------------------------------------------------------------------
# Hero
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="cm-hero">
      <div class="cm-eyebrow">Your next movie night starts here</div>
      <div class="cm-brand">🎬 CineMatch <span class="accent">AI</span></div>
      <div class="cm-tagline">Discover movies that match your taste.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Search panel
with st.container(border=True):
    st.markdown('<div class="cm-section-title">🔎 Find your next favourite</div>', unsafe_allow_html=True)
    st.markdown('<div class="cm-section-subtitle">Enter a movie you love and we’ll find titles with a similar feel.</div>', unsafe_allow_html=True)

    movie_name = st.text_input(
        "Movie title",
        placeholder="e.g. The Dark Knight, Interstellar, Inception",
        label_visibility="collapsed",
    )
    num_recommendations = st.slider(
        "How many movies do you want to discover?",
        min_value=5,
        max_value=20,
        value=10,
        help="Choose how many movies CineMatch should recommend.",
    )
    recommend_button = st.button("🎬  Find Similar Movies", type="primary", use_container_width=True)


# -----------------------------------------------------------------------------
# Request recommendations
# -----------------------------------------------------------------------------
if recommend_button:
    cleaned_name = movie_name.strip()
    if not cleaned_name:
        st.warning("Enter a movie title to get recommendations.")
    else:
        payload = {
            "movie_name": cleaned_name,
            "n_recommendations": num_recommendations,
        }
        with st.spinner("Matching movies to your taste…"):
            try:
                response = requests.post(RECOMMEND_ENDPOINT, json=payload, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.recommendations = data.get("recommendations", [])
                    st.session_state.searched_movie = data.get("searched_movie", cleaned_name)
                else:
                    try:
                        detail = response.json().get("detail", "The recommendation request failed.")
                    except ValueError:
                        detail = "The recommendation service returned an unexpected response."
                    st.error(f"{detail} (HTTP {response.status_code})")
            except requests.RequestException as exc:
                st.error("Could not reach the recommendation API. Check that your FastAPI backend is running.")
                st.caption(str(exc))


# -----------------------------------------------------------------------------
# Recommendation cards
# -----------------------------------------------------------------------------
recommendations = st.session_state.recommendations
if recommendations:
    safe_searched_movie = html.escape(str(st.session_state.searched_movie))
    st.markdown(
        f"""
        <div class="cm-result-banner">
          <div class="cm-result-label">Your movie match</div>
          <div class="cm-result-title">Recommendations inspired by <span>{safe_searched_movie}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="cm-section-title">Recommended for you</div>', unsafe_allow_html=True)
    st.markdown('<div class="cm-section-subtitle">A hand-picked lineup based on movie similarity and other ranking signals.</div>', unsafe_allow_html=True)

    # Movie details panel for the selected recommendation
    selected_movie_id = st.session_state.selected_movie_id
    if selected_movie_id is not None:
        st.markdown("---")
        detail_col, close_col = st.columns([5, 1])
        with detail_col:
            st.markdown('<div class="cm-section-title">Movie details</div>', unsafe_allow_html=True)
        with close_col:
            if st.button("✕ Close", key="close_movie_details", use_container_width=True):
                st.session_state.selected_movie_id = None
                st.rerun()

        with st.spinner("Loading movie details…"):
            details = get_movie_details(selected_movie_id)

        if details:
            detail_title = html.escape(str(details.get("title") or "Movie details"))
            detail_overview = html.escape(
                str(details.get("overview") or "No overview is available for this movie.")
            )
            backdrop_path = details.get("backdrop_path")
            backdrop_url = f"{IMAGE_BASE_URL}/w1280{backdrop_path}" if backdrop_path else None
            detail_poster_path = details.get("poster_path")
            detail_poster_url = (
                f"{IMAGE_BASE_URL}/w500{detail_poster_path}" if detail_poster_path else None
            )
            detail_genres = [
                html.escape(str(genre.get("name", "")))
                for genre in details.get("genres", [])
                if isinstance(genre, dict) and genre.get("name")
            ]
            detail_release = html.escape(str(details.get("release_date") or "Release date unavailable"))
            detail_rating = details.get("vote_average")

            if backdrop_url:
                st.image(backdrop_url, use_container_width=True)

            info_col, poster_col = st.columns([3, 1], gap="large")
            with info_col:
                st.markdown(f'<div class="cm-result-title">{detail_title}</div>', unsafe_allow_html=True)
                meta_parts = [f"📅 {detail_release}"]
                if detail_rating is not None:
                    try:
                        meta_parts.append(f"⭐ {float(detail_rating):.1f}/10")
                    except (TypeError, ValueError):
                        pass
                st.markdown(
                    f'<div class="cm-meta">{" &nbsp; · &nbsp; ".join(meta_parts)}</div>',
                    unsafe_allow_html=True,
                )
                if detail_genres:
                    st.markdown(
                        " ".join(
                            f'<span style="display:inline-block;background:#292c39;border:1px solid rgba(255,255,255,.1);'
                            f'border-radius:999px;padding:5px 10px;margin:8px 5px 8px 0;font-size:.8rem;">{genre}</span>'
                            for genre in detail_genres
                        ),
                        unsafe_allow_html=True,
                    )
                st.markdown("**Overview**")
                st.write(details.get("overview") or "No overview is available for this movie.")
            with poster_col:
                if detail_poster_url:
                    st.image(detail_poster_url, use_container_width=True)
        else:
            st.warning("Couldn't load details right now. Please try again.")



    columns_per_row = 5 if len(recommendations) >= 5 else len(recommendations)
    columns_per_row = max(1, columns_per_row)

    for start in range(0, len(recommendations), columns_per_row):
        row_movies = recommendations[start : start + columns_per_row]
        cols = st.columns(columns_per_row, gap="medium")

        for col, movie in zip(cols, row_movies):
            with col:
                with st.container(border=True):
                    title = str(movie.get("title") or "Untitled movie")
                    safe_title = html.escape(title)
                    movie_id = movie.get("id")

                    poster = None
                    if movie_id is not None:
                        try:
                            poster = get_poster(movie_id)
                        except Exception:
                            poster = None

                    if poster:
                        st.image(poster, use_container_width=True)
                    else:
                        st.markdown(
                            """
                            <div style="aspect-ratio:2/3;display:flex;flex-direction:column;align-items:center;justify-content:center;
                                        text-align:center;background:linear-gradient(145deg,#292c39,#151720);border-radius:10px;
                                        border:1px solid rgba(255,255,255,.08);padding:1rem;color:#a6a9b5;">
                              <div style="font-size:2.2rem">🎞️</div>
                              <div style="font-weight:700;margin-top:.5rem">Poster unavailable</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    st.markdown(f'<div class="cm-card-title">{safe_title}</div>', unsafe_allow_html=True)

                    rating = movie.get("vote_average")
                    if rating is not None:
                        try:
                            st.markdown(f'<div class="cm-meta">⭐ <b>{float(rating):.1f}</b> <span style="color:#777b89">/ 10 IMDb rating</span></div>', unsafe_allow_html=True)
                        except (TypeError, ValueError):
                            pass

                    release_date = str(movie.get("release_date") or "")
                    release_year = release_date[:4] if len(release_date) >= 4 else "Year unknown"
                    popularity = movie.get("popularity")
                    st.markdown(f'<div class="cm-meta">📅 {html.escape(release_year)}</div>', unsafe_allow_html=True)
                    if popularity is not None:
                        try:
                            st.markdown(f'<div class="cm-meta">🔥 Popularity {float(popularity):.1f}</div>', unsafe_allow_html=True)
                        except (TypeError, ValueError):
                            pass

                    similarity = movie.get("similarity")
                    if similarity is not None:
                        try:
                            similarity_pct = max(0.0, min(100.0, float(similarity) * 100))
                            st.markdown(
                                f"""
                                <div class="cm-score-wrap">
                                  <div class="cm-score-label"><span>🎯 Similarity</span><b>{similarity_pct:.1f}%</b></div>
                                  <div class="cm-score-track"><div class="cm-score-fill" style="width:{similarity_pct:.1f}%"></div></div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        except (TypeError, ValueError):
                            pass

                    final_score = movie.get("final_score")
                    if final_score is not None:
                        try:
                            st.caption(f"Ranking score: {float(final_score):.3f}")
                        except (TypeError, ValueError):
                            pass

                    if movie_id is not None:
                        if st.button(
                            "View Details",
                            key=f"view_details_{movie_id}",
                            use_container_width=True,
                        ):
                            st.session_state.selected_movie_id = int(movie_id)
                            st.rerun()


elif recommend_button is False and not st.session_state.searched_movie:
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.info("Enter a movie title above and select **Find Similar Movies** to get started.")


# -----------------------------------------------------------------------------
# Sidebar and footer
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🎬 CineMatch AI")
    st.caption("A smarter way to choose your next movie.")
    st.divider()
    st.markdown("**How it works**")
    st.write("CineMatch uses content-based movie features to find titles similar to the one you enter.")
    st.markdown("**Powered by**")
    st.write("Python · FastAPI · Streamlit · Scikit-learn · TMDB")
    st.divider()
    st.caption("Built by Pushkar Sharma")


# ============================================================
# Footer
# ============================================================


# ============================================================
# Footer
# ============================================================

st.markdown(
    """
    <div class="app-footer">
        <span class="footer-brand">CineMatch <span>AI</span></span>
        <span class="footer-divider">·</span>
        <span>Find your next favourite film.</span>
    </div>
    """,
    unsafe_allow_html=True,
)
