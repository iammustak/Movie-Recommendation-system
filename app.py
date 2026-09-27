import streamlit as st
import pickle
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.movie-title {
    font-size: 20px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# TMDB API KEY
# =========================================================

API_KEY = "f560a9a747413ba1e76937b3b985f905"

# India
REGION = "IN"


# =========================================================
# REQUEST SESSION + RETRY
# =========================================================

session = requests.Session()

retry_strategy = Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(
    max_retries=retry_strategy
)

session.mount("https://", adapter)
session.mount("http://", adapter)

session.headers.update({
    "User-Agent": "Movie-Recommender-App/1.0"
})


# =========================================================
# LOAD MODEL
# =========================================================

movies = pickle.load(
    open("movies.pkl", "rb")
)

similarity = pickle.load(
    open("similarity.pkl", "rb")
)


# =========================================================
# FETCH MOVIE DETAILS
# =========================================================

@st.cache_data(ttl=3600)
def fetch_movie_details(movie_id):

    url = f"https://api.themoviedb.org/3/movie/{movie_id}"

    params = {
        "api_key": API_KEY
    }

    try:

        response = session.get(
            url,
            params=params,
            timeout=15
        )

        if response.status_code != 200:
            return None

        return response.json()

    except requests.exceptions.RequestException:
        return None


# =========================================================
# FETCH POSTER
# =========================================================

def fetch_poster(movie_id):

    data = fetch_movie_details(movie_id)

    if data:

        poster_path = data.get("poster_path")

        if poster_path:

            return (
                "https://image.tmdb.org/t/p/w500"
                + poster_path
            )

    return None


# =========================================================
# FETCH TRAILER
# =========================================================

@st.cache_data(ttl=3600)
def fetch_trailer(movie_id):

    url = (
        f"https://api.themoviedb.org/3/movie/"
        f"{movie_id}/videos"
    )

    params = {
        "api_key": API_KEY
    }

    try:

        response = session.get(
            url,
            params=params,
            timeout=15
        )

        if response.status_code != 200:
            return None

        data = response.json()

        videos = data.get("results", [])

        # Official YouTube Trailer
        for video in videos:

            if (
                video.get("site") == "YouTube"
                and video.get("type") == "Trailer"
                and video.get("official") is True
            ):

                key = video.get("key")

                return (
                    f"https://www.youtube.com/watch?v={key}"
                )

        # Normal YouTube Trailer
        for video in videos:

            if (
                video.get("site") == "YouTube"
                and video.get("type") == "Trailer"
            ):

                key = video.get("key")

                return (
                    f"https://www.youtube.com/watch?v={key}"
                )

        return None

    except requests.exceptions.RequestException:
        return None


# =========================================================
# HERE TO WATCH
# =========================================================

@st.cache_data(ttl=3600)
def fetch_watch_providers(movie_id):

    url = (
        f"https://api.themoviedb.org/3/movie/"
        f"{movie_id}/watch/providers"
    )

    params = {
        "api_key": API_KEY
    }

    try:

        response = session.get(
            url,
            params=params,
            timeout=15
        )

        if response.status_code != 200:
            return None

        data = response.json()

        country_data = data.get(
            "results",
            {}
        ).get(
            REGION
        )

        if not country_data:
            return None

        providers = []

        # Streaming
        for provider in country_data.get(
            "flatrate",
            []
        ):

            providers.append(
                provider
            )

        # Rent
        for provider in country_data.get(
            "rent",
            []
        ):

            if provider not in providers:
                providers.append(
                    provider
                )

        # Buy
        for provider in country_data.get(
            "buy",
            []
        ):

            if provider not in providers:
                providers.append(
                    provider
                )

        link = country_data.get(
            "link"
        )

        return {
            "providers": providers,
            "link": link
        }

    except requests.exceptions.RequestException:
        return None


# =========================================================
# RECOMMEND MOVIES
# =========================================================

def recommend(movie):

    movie_index = movies[
        movies["title"] == movie
    ].index[0]

    distances = similarity[movie_index]

    # 10 recommendations
    movie_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:11]

    recommended_movies = []
    recommended_posters = []
    recommended_details = []
    recommended_trailers = []
    recommended_watch = []

    for i in movie_list:

        movie_id = movies.iloc[
            i[0]
        ].movie_id

        movie_title = movies.iloc[
            i[0]
        ].title

        # Movie name
        recommended_movies.append(
            movie_title
        )

        # Details
        details = fetch_movie_details(
            movie_id
        )

        recommended_details.append(
            details
        )

        # Poster
        poster = fetch_poster(
            movie_id
        )

        recommended_posters.append(
            poster
        )

        # Trailer
        trailer = fetch_trailer(
            movie_id
        )

        recommended_trailers.append(
            trailer
        )

        # Here to Watch
        watch = fetch_watch_providers(
            movie_id
        )

        recommended_watch.append(
            watch
        )

    return (
        recommended_movies,
        recommended_posters,
        recommended_details,
        recommended_trailers,
        recommended_watch
    )


# =========================================================
# HEADER
# =========================================================

st.title("🎬 Movie Recommender System")

st.write(
    "Discover movies similar to your favourite movie."
)

st.divider()


# =========================================================
# MOVIE SELECTOR
# =========================================================

selected_movie = st.selectbox(
    "🎥 Select a movie",
    movies["title"].values
)


# =========================================================
# RECOMMEND BUTTON
# =========================================================

if st.button(
    "🍿 Recommend Movies",
    use_container_width=True
):

    with st.spinner(
        "Finding amazing movies for you..."
    ):

        (
            names,
            posters,
            details,
            trailers,
            watch_data
        ) = recommend(
            selected_movie
        )

    st.success(
        f"10 movies similar to {selected_movie}"
    )

    st.divider()


    # =====================================================
    # 10 MOVIES → 5 + 5
    # =====================================================

    for start in range(0, 10, 5):

        cols = st.columns(5)

        for i in range(5):

            index = start + i

            with cols[i]:

                # -----------------------------------------
                # MOVIE NAME
                # -----------------------------------------

                st.markdown(
                    f"### 🎬 {names[index]}"
                )


                # -----------------------------------------
                # POSTER
                # -----------------------------------------

                if posters[index]:

                    st.image(
                        posters[index],
                        use_container_width=True
                    )

                else:

                    st.info(
                        "Poster not available"
                    )


                # -----------------------------------------
                # RATING
                # -----------------------------------------

                movie_data = details[index]

                if movie_data:

                    rating = movie_data.get(
                        "vote_average",
                        0
                    )

                    st.write(
                        f"⭐ **{rating:.1f}/10**"
                    )


                    # -------------------------------------
                    # GENRE
                    # -------------------------------------

                    genres = movie_data.get(
                        "genres",
                        []
                    )

                    genre_names = ", ".join(
                        [
                            genre["name"]
                            for genre in genres
                        ]
                    )

                    if genre_names:

                        st.write(
                            f"🎭 **{genre_names}**"
                        )


                # -----------------------------------------
                # WATCH TRAILER
                # -----------------------------------------

                if trailers[index]:

                    st.link_button(
                        "▶️ Watch Trailer",
                        trailers[index],
                        use_container_width=True
                    )

                else:

                    st.caption(
                        "🎞️ Trailer not available"
                    )


                # -----------------------------------------
                # HERE TO WATCH
                # -----------------------------------------

                watch = watch_data[index]

                if watch and watch.get(
                    "providers"
                ):

                    st.write(
                        "🍿 **Here to Watch**"
                    )

                    providers = watch[
                        "providers"
                    ]

                    # Show provider names
                    provider_names = []

                    for provider in providers[:5]:

                        provider_names.append(
                            provider.get(
                                "provider_name"
                            )
                        )

                    st.caption(
                        " • ".join(
                            provider_names
                        )
                    )

                    # Legal streaming/rental page
                    if watch.get("link"):

                        st.link_button(
                            "🍿 Here to Watch",
                            watch["link"],
                            use_container_width=True
                        )

                else:

                    st.caption(
                        "🍿 Where to watch not available"
                    )


        st.divider()


# =========================================================
# TMDB ATTRIBUTION
# =========================================================

st.caption(
    "Movie data and images provided by TMDB. "
    "This product uses the TMDB API but is not endorsed or certified by TMDB."
)