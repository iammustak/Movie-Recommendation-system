import streamlit as st
import pickle
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import quote


# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Movie Recommendation",
    page_icon="🎬",
    layout="wide"
)


# ---------------- TMDB API KEY ----------------

API_KEY = "f560a9a747413ba1e76937b3b985f905"


# ---------------- LOAD DATA ----------------

movies = pickle.load(open("movies.pkl", "rb"))
similarity = pickle.load(open("similarity.pkl", "rb"))


# ---------------- REQUEST SESSION ----------------

session = requests.Session()

retry = Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(max_retries=retry)

session.mount("https://", adapter)


# ---------------- CSS ----------------

st.markdown("""
<style>

.movie-title {
    height: 55px;
    text-align: center;
    font-size: 17px;
    font-weight: bold;
    margin-bottom: 10px;
}

.movie-poster {
    width: 100%;
    height: 300px;
    overflow: hidden;
    border-radius: 10px;
}

.movie-poster img {
    width: 100%;
    height: 300px;
    object-fit: cover;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)


# ---------------- FETCH POSTER ----------------

@st.cache_data(ttl=3600)
def fetch_poster(movie_name):

    url = "https://api.themoviedb.org/3/search/movie"

    params = {
        "api_key": API_KEY,
        "query": movie_name
    }

    try:

        response = session.get(
            url,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        if results:

            poster_path = results[0].get("poster_path")

            if poster_path:

                return (
                    "https://image.tmdb.org/t/p/w500"
                    + poster_path
                )

        return None

    except requests.exceptions.RequestException:

        return None


# ---------------- TRAILER LINK ----------------

def trailer_link(movie_name):

    query = quote(movie_name + " official trailer")

    return f"https://www.youtube.com/results?search_query={query}"


# ---------------- WATCH MOVIE LINK ----------------

def watch_movie_link(movie_name):

    query = quote(movie_name + " watch online")

    return f"https://www.google.com/search?q={query}"


# ---------------- RECOMMEND FUNCTION ----------------

def recommend(movie):

    movie_index = movies[
        movies["title"] == movie
    ].index[0]

    distances = similarity[movie_index]

    movie_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:11]

    recommended_movies = []

    for i in movie_list:

        movie_index = i[0]

        movie_name = movies.iloc[movie_index].title

        recommended_movies.append(movie_name)

    return recommended_movies


# ---------------- MAIN UI ----------------

st.title("🎬 Movie Recommendation System")




# ---------------- SELECT MOVIE ----------------

selected_movie = st.selectbox(
    "🎥 Select a movie",
    movies["title"].values
)


# ---------------- RECOMMEND BUTTON ----------------

if st.button(
    "🍿 Recommend",
    use_container_width=True
):

    names = recommend(selected_movie)


    # ---------------- FIRST ROW ----------------

    for start in range(0, 10, 5):

        cols = st.columns(5)

        for i in range(5):

            index = start + i

            with cols[i]:

                movie_name = names[index]


                # Movie title

                st.markdown(
                    f"""
                    <div class="movie-title">
                        {movie_name}
                    </div>
                    """,
                    unsafe_allow_html=True
                )


                # Poster

                poster = fetch_poster(movie_name)

                if poster:

                    st.markdown(
                        f"""
                        <div class="movie-poster">
                            <img src="{poster}">
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                else:

                    st.image(
                        "https://placehold.co/500x750?text=No+Poster",
                        use_container_width=True
                    )


                # Trailer button

                st.link_button(
                    "🎬 Watch Trailer",
                    trailer_link(movie_name),
                    use_container_width=True
                )


                # Watch movie button

                st.link_button(
                    "🍿 Watch Movie",
                    watch_movie_link(movie_name),
                    use_container_width=True
                )