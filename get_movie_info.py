from dotenv import load_dotenv
import requests
import os

# https://developer.themoviedb.org/docs/getting-started

# https://www.themoviedb.org/settings/api

# https://medium.com/@mcasciato/no-imdb-api-check-out-these-options-75917d0fe923

def tmdb_info(movie_name, tmdb_api_key):
    """
    Fetches movie information from TMDB API.

    :param movie_name: Name of the movie to search for.
    :param api_key: Your TMDB API key.
    :return: Dictionary containing movie information or None if not found.
    """
    with requests.Session() as session:
        base_url = "https://api.themoviedb.org/3"
        query_url = f"{base_url}/search/movie?api_key={tmdb_api_key}&query={movie_name}"
        query_response = session.get(query_url)

        if query_response.status_code == 200:
            data = query_response.json()
            if data['results']:
                query_result = data['results'][0]  # Return the first result
                tmdb_id = query_result['id']
                movie_url = f"{base_url}/movie/{tmdb_id}?api_key={tmdb_api_key}"
                movie_response = session.get(movie_url)

                if movie_response.status_code == 200:
                    movie_data = movie_response.json()
                    movie_info = {
                        'title': movie_data['original_title'],
                        'tmdb_id': movie_data['id'],
                        'imdb_id': movie_data['imdb_id'],
                        'genres': [genre['name'] for genre in movie_data['genres']],
                        'release_date': movie_data['release_date'],
                        'overview': movie_data['overview'],
                        'poster_path': f"https://image.tmdb.org/t/p/w500{movie_data['poster_path']}",
                        'backdrop_path': f"https://image.tmdb.org/t/p/w500{movie_data['backdrop_path']}",
                        'rating': movie_data['vote_average'],
                        'runtime': movie_data['runtime']
                    }
                    return movie_info
            else:
                print("No results found.")
                return None
        else:
            print(f"Error: {query_response.status_code}")
            return None

if __name__ == '__main__':
    print(tmdb_info("Inception", os.getenv('TMDB_API_KEY')))
