from dotenv import load_dotenv
import requests
import os

# https://developer.themoviedb.org/docs/getting-started

# https://www.themoviedb.org/settings/api

# https://medium.com/@mcasciato/no-imdb-api-check-out-these-options-75917d0fe923

def tmdb_info(movie_name, tmdb_api_key=os.getenv('TMDB_API_KEY', None)):
    """
    Fetches movie information from TMDB API.

    :param movie_name: Name of the movie to search for.
    :param api_key: Your TMDB API key.
    :return: Dictionary containing movie information or None if not found.
    """
    if tmdb_api_key is None:
        print("TMDB API key not provided.")
        return None
    
    with requests.Session() as session:
        base_url = "https://api.themoviedb.org/3"
        query_url = f"{base_url}/search/movie?api_key={tmdb_api_key}&query={movie_name}"
        query_response = session.get(query_url)

        if query_response.status_code == 200:
            data = query_response.json()
            if data['results']:
                query_result = data['results'][0]  # Return the first result
                tmdb_id = query_result['id']
                movie_url = f"{base_url}/movie/{tmdb_id}?api_key={tmdb_api_key}&append_to_response=credits"
                movie_response = session.get(movie_url)

                if movie_response.status_code == 200:
                    movie_data = movie_response.json()
                    cast = []
                    director = None
                    for crew_member in movie_data['credits']['crew']:
                        if crew_member['job'] == 'Director':
                            director = {
                                'name': crew_member['name'],
                                'original_name': crew_member['original_name'],
                                'tmdb_id': crew_member['id'],
                                'profile_path': f"https://image.tmdb.org/t/p/w500{crew_member['profile_path']}" if crew_member['profile_path'] else None,
                                'gender': crew_member['gender'],
                                'credit_id': crew_member['credit_id'],
                                'tmdb_id': crew_member['id']
                            }
                            break
                    for cast_member in movie_data['credits']['cast']:
                        cast.append({
                            'name': cast_member['name'],
                            'original_name': cast_member['original_name'],
                            'tmdb_id': cast_member['id'],
                            'profile_path': f"https://image.tmdb.org/t/p/w500{cast_member['profile_path']}" if cast_member['profile_path'] else None,
                            'gender': cast_member['gender'],
                            'credit_id': cast_member['credit_id'],
                            'character_name': cast_member['character'],
                            'credit_order': cast_member['order'],
                            'cast_id': cast_member['cast_id'],
                        })
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
                        'runtime': movie_data['runtime'],
                        'director': director,
                        'cast': cast
                    }
                    return movie_info
            else:
                print("No results found.")
                return None
        else:
            print(f"Error: {query_response.status_code}")
            return None

if __name__ == '__main__':
    print(tmdb_info("Inception"))
