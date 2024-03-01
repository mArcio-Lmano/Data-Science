import requests
import sqlite3
import json

from bs4 import BeautifulSoup
from datetime import datetime


class Actor:
    def __init__(self, name) -> None:
        self.name = name

class Movie:
    def __init__(self, 
                 name, 
                 link, 
                 rating_IMDB, 
                 rating_MPPA,
                 year,
                 duration, 
                 genres,
                 director = None, 
                 language = None,
                 actors = None) -> None:
        
        self.name = name 
        self.link = link 
        self.rating_IMDB = rating_IMDB.text if rating_IMDB else rating_IMDB
        self.rating_MPPA = rating_MPPA
        self.year = year
        self.released = "Yes" if rating_IMDB else "No"
        self.duration = duration
        self.genres = genres
        self.director = director
        self.language = language
        self.actors = actors
        self.add_to_db_date = datetime.now().date()
        
    
    def printMovie(self) -> None:
        console_strig = f"""Name: {self.name}
    Link:        {self.link}
    IMBD Rating: {self.rating_IMDB}
    MPPA Rating: {self.rating_MPPA}
    Year:        {self.year},
    Released yet: {self.released}
    Duration:    {self.duration}
    Added to the personal database: {self.add_to_db_date}
        Genres:   {self.genres}
        Director: {self.director}
        Language: {self.language}
        """
        print(console_strig)
        return None


def getPopularMovies() -> list:
    
    url = "https://www.imdb.com/chart/moviemeter/?ref_=nv_mv_mpm"
    
    with open("headers.json", "r") as f:
        headers = json.load(f)
    response = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    movies_html_list = soup.find_all("li", class_="ipc-metadata-list-summary-item sc-1364e729-0 caNpAE cli-parent")
    
    movies = []
    for movie_html in movies_html_list:
        a_tag = movie_html.find("a", class_="ipc-title-link-wrapper")
        movie_name = a_tag.h3.text
        link_aux = a_tag["href"].split("/")
        movie_link = "https://www.imdb.com/title/" + link_aux[2]
        
        movie_rating_IMDB = movie_html.find("span", class_="ipc-rating-star ipc-rating-star--base ipc-rating-star--imdb ratingGroup--imdb-rating")
        movie_infos = movie_html.find_all("span", class_="sc-be6f1408-8 fcCUPU cli-title-metadata-item")
        movies_infos_text = []
        for i in range(3):
            if i >= len(movie_infos):
                movies_infos_text.append(None)
            else:
                movies_infos_text.append(movie_infos[i].text)
        
        movie_request = requests.get(url=movie_link, headers=headers)
        if movie_request.status_code == 200:
            movie_soup = BeautifulSoup(movie_request.text, "html.parser")
            movie_soup_genres = movie_soup.find(attrs={"data-testid": "genres"})
            movie_genres_html = movie_soup_genres.find_all("span", class_="ipc-chip__text")
            movie_genres = [movie_genre.text for movie_genre in movie_genres_html]
            
            movie_director_html = movie_soup.find_all("li", class_="ipc-metadata-list__item", attrs={"data-testid": "title-pc-principal-credit"})[0]
            movie_director = movie_director_html.find("a", class_="ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link").text

            movie_soup_language = movie_soup.find_all("div", class_="sc-f65f65be-0 bBlII", attrs={"data-testid": "title-details-section"})[0]
            movie_soup_language = movie_soup_language.find("li", {"data-testid": "title-details-languages"})
            movie_language = movie_soup_language.find("a", class_="ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link").text
        
            movie = Movie(name=movie_name,
                        link=movie_link,
                        rating_IMDB=movie_rating_IMDB,
                        rating_MPPA=movies_infos_text[2],
                        year=movies_infos_text[0],
                        duration=movies_infos_text[1],
                        genres=movie_genres,
                        director=movie_director,
                        language=movie_language)
            
            # movie.printMovie()
            
            movies.append(movie)
        elif movie_request.status_code == 504:
            print(f"Gateway Timeout Error for the movie: {movie_name}")    
    
    return movies

def create_movies_table(cursor):
    cursor.execute("""CREATE TABLE IF NOT EXISTS movies (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        link TEXT,
                        rating_IMDB TEXT,
                        rating_MPPA TEXT,
                        year INTEGER,
                        released TEXT,
                        duration TEXT,
                        genres TEXT,
                        director TEXT,
                        language TEXT,
                        actors TEXT,
                        add_to_db_date DATE
                    )""")

def insert_movie(cursor, movie):
    genres_str = ', '.join(movie.genres) if movie.genres else None
    cursor.execute("""INSERT INTO movies (
                        name,
                        link,
                        rating_IMDB,
                        rating_MPPA,
                        year,
                        released,
                        duration,
                        genres,
                        director,
                        language,
                        actors,
                        add_to_db_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (movie.name, movie.link, movie.rating_IMDB, movie.rating_MPPA,
                     movie.year, movie.released, movie.duration, genres_str,
                     movie.director, movie.language, movie.actors, movie.add_to_db_date))
def main():
    movies = getPopularMovies()
    
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()

    create_movies_table(cursor)
    print(len(movies))
    for movie in movies:
        insert_movie(cursor, movie)

    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    main() 
