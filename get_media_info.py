import requests
import os
import json

# https://developer.themoviedb.org/docs/getting-started

# https://www.themoviedb.org/settings/api

# https://medium.com/@mcasciato/no-imdb-api-check-out-these-options-75917d0fe923

def store_media_info(movie_info, output_file='movie-info.json'):
    # Load existing movies or create new array
    try:
        with open(output_file, 'r') as f:
            movies = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        movies = []
    
    for movie in movies:
        if movie['title'] == movie_info['title']:
            print(f"Movie {movie_info['title']} has already been added")
            return

    # Append new movie info
    movies.append(movie_info)

    with open(output_file, 'w') as f:
        json.dump(movies, f, indent=2)

def get_director(crew):
    for crew_member in crew:
        if crew_member['job'] == 'Director':
            return {
                'name': crew_member['name'],
                'original_name': crew_member['original_name'],
                'tmdb_id': crew_member['id'],
                'profile_path': f"https://image.tmdb.org/t/p/w500{crew_member['profile_path']}" if crew_member['profile_path'] else None,
                'gender': crew_member['gender'],
                'tmdb_credit_id': crew_member['credit_id'],
                'tmdb_id': crew_member['id']
            }
    return None

def tmdb_tv_info(tv_name, tmdb_api_key=os.getenv('TMDB_API_KEY', None)):
    """
    Fetches TV show information from TMDB API.

    :param tv_name: Name of the TV show to search for.
    :param api_key: Your TMDB API key.
    :return: Dictionary containing TV show information or None if not found.
    """
    if tmdb_api_key is None:
        print("TMDB API key not provided.")
        return None
    
    with requests.Session() as session:
        base_url = "https://api.themoviedb.org/3"
        query_url = f"{base_url}/search/tv?api_key={tmdb_api_key}&query={tv_name}"
        query_response = session.get(query_url)

        if query_response.status_code == 200:
            data = query_response.json()
            if data['results']:
                query_result = data['results'][0]  # Return the first result
                tmdb_id = query_result['id']
                tv_url = f"{base_url}/tv/{tmdb_id}?api_key={tmdb_api_key}&append_to_response=credits"
                tv_response = session.get(tv_url)
                if tv_response.status_code == 200:
                    tv_data = tv_response.json()
                    series_id = tv_data['id']
                    tv_info = {
                        'title': tv_data['original_name'],
                        'tmdb_id': series_id,
                        'genres': [genre['name'] for genre in tv_data['genres']],
						'release_date': tv_data['first_air_date'],
                        'overview': tv_data['overview'],
                        'poster_path': f"https://image.tmdb.org/t/p/w500{tv_data['poster_path']}",
                        'backdrop_path': f"https://image.tmdb.org/t/p/w500{tv_data['backdrop_path']}",
                        'rating': tv_data['vote_average'],
                        'number_of_seasons': tv_data['number_of_seasons'],
                        'number_of_episodes': tv_data['number_of_episodes'],
                        'seasons': [],
                        'specials': {}
                    }

                    seasons = []

                    for season in tv_data['seasons']:
                        season_number = season['season_number']
                        episodes = []

                        for i in range(season['episode_count']):
                            episode_url = f"{base_url}/tv/{series_id}/season/{season_number}/episode/{i+1}?api_key={tmdb_api_key}"
                            episode_response = session.get(episode_url)
                            if episode_response.status_code == 200:
                                episode_data = episode_response.json()
                                guest_stars = []
                                for guest_star in episode_data['guest_stars']:
                                    guest_stars.append({
                                        'name': guest_star['name'],
                                        'original_name': guest_star['original_name'],
                                        'tmdb_id': guest_star['id'],
                                        'profile_path': f"https://image.tmdb.org/t/p/w500{guest_star['profile_path']}" if guest_star['profile_path'] else None,
                                        'gender': guest_star['gender'],
                                        'tmdb_credit_id': guest_star['credit_id'],
                                        'character_name': guest_star['character'],
                                        'credit_order': guest_star['order']
                                    })
                                    
                                episodes.append({
                                    'episode_number': episode_data['episode_number'],
                                    'air_date': episode_data['air_date'],
                                    'overview': episode_data['overview'],
                                    'still_path': f"https://image.tmdb.org/t/p/w500{episode_data['still_path']}" if episode_data['still_path'] else None,
                                    'tmdb_id': episode_data['id'],
                                    'name': episode_data['name'],
                                    'rating': episode_data['vote_average'],
                                    'director': get_director(episode_data['crew']),
                                    'guest_stars': guest_stars
                                })
                        
                        print(season)
                        flatten_season = {
                            'season_number': season_number,
                            'air_date': season['air_date'], # convert to datetime object
                            'overview': season['overview'],
                            'poster_path': f"https://image.tmdb.org/t/p/w500{season['poster_path']}" if season['poster_path'] else None,
                            'season_id': season['id'],
                            'episodes': episodes,
                            'title': season['name'],
                            'rating': season['vote_average']
                        }
                        
                        flatten_season['episodes'] = episodes

                        # Season Number 0, contains information about specials and is stored separately from the rest of the seasons
                        if season_number == 0:
                            tv_info['specials'] = flatten_season
                        else:
                            seasons.append(flatten_season)
                    tv_info['seasons'] = seasons
                return tv_info
            else:
                print("No results found.")
                return None
        else:
            print(f"Error: {query_response.status_code}")
            return None

def tmdb_movie_info(movie_name, tmdb_api_key=os.getenv('TMDB_API_KEY', None)):
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
                    director = get_director(movie_data['credits']['crew'])
                    for cast_member in movie_data['credits']['cast']:
                        cast.append({
                            'name': cast_member['name'],
                            'original_name': cast_member['original_name'],
                            'tmdb_id': cast_member['id'],
                            'profile_path': f"https://image.tmdb.org/t/p/w500{cast_member['profile_path']}" if cast_member['profile_path'] else None,
                            'gender': cast_member['gender'],
                            'tmdb_credit_id': cast_member['credit_id'],
                            'character_name': cast_member['character'],
                            'credit_order': cast_member['order'],
                            'tmdb_cast_id': cast_member['cast_id'],
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
    tv = tmdb_tv_info("Band of Brothers")
    print(tv)
    store_media_info(tv, 'test-tvshow.json')

    print()

    movie = tmdb_movie_info("Inception")
    print(movie)
    store_media_info(movie, 'test-movie.json')
