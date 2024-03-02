import pandas as pd
import requests
import sqlite3
import json
import sys

from bs4 import BeautifulSoup
from datetime import datetime
from tabulate import tabulate



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
                 director, 
                 language,
                 actors = None,
                 seen = None) -> None:
        
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
        self.seen = seen
        
    
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
        Seen: {self.seen}
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
                        add_to_db_date DATE,
                        seen DATE
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
                        add_to_db_date,
                        seen
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (movie.name, movie.link, movie.rating_IMDB, movie.rating_MPPA,
                     movie.year, movie.released, movie.duration, genres_str,
                     movie.director, movie.language, movie.actors, movie.add_to_db_date, movie.seen))


def get_column_names(table_name):
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    
    cursor.execute(f"PRAGMA table_info({table_name})")
    
    columns = cursor.fetchall()
    
    column_names = [column[1] for column in columns]
    
    conn.close()
    
    return column_names

def update_seen(cursor, movie_name):
    cursor.execute(f"""
            SELECT seen FROM movies
            WHERE name = '{movie_name}'
        """)
    result = cursor.fetchone()
    if result and result[0] is not None:
        user_input = input(f"You already seen this movie in {result[0]}. Do you want to update it anyway? [y/n]: ")
        if user_input.lower() != 'y':
            print("Update aborted.")
            return
    seen_date = datetime.now().date()
    cursor.execute(f"""
        UPDATE movies
        SET seen = '{seen_date}'
        WHERE name = '{movie_name}'
    """)
    
    cursor.execute(f"""
                   SELECT * FROM movies 
                   WHERE name = '{movie_name}'
        """)
    
    movie_info = cursor.fetchall()
    
    movie = Movie(name=movie_info[1],
                  link=movie_info[2],
                  rating_IMDB=movie_info[3],
                  rating_MPPA=movie_info[4],
                  year=movie_info[5],
                  duration=movie_info[6],
                  genres=movie_info[7],
                  director=movie_info[8],
                  language=movie_info[9],
                  actors=movie_info[10]
                  )
    
    movie.printMovie()

def main():
    create_flag = "--new" in sys.argv
    update_seen_flag = "--update-seen" in sys.argv
    list_movies_flag = "--list-movies" in sys.argv
    if create_flag:
        user_flag = input("Are you sure you want to continue?[Y/n] ")
        if user_flag.lower() == 'y':
            movies = getPopularMovies()
        
            conn = sqlite3.connect("movies.db")
            cursor = conn.cursor()

            create_movies_table(cursor)

            for movie in movies:
                insert_movie(cursor, movie)

            conn.commit()
            conn.close()
        else:
            print("Database creation aborted.")
    
    elif list_movies_flag:
        conn = sqlite3.connect("movies.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, rating_IMDB FROM movies")
        movies = cursor.fetchall()
        conn.close()
        
        movies_names = [movie[0] for movie in movies]
        movies_rating_IMDB = [movie[1] for movie in movies]
        
        half_len = len(movies) // 2 + 1
        movies_names_1 = movies_names[:half_len]
        movies_names_2 = movies_names[half_len:]
        
        movies_rating_IMDB_1 = movies_rating_IMDB[:half_len]
        movies_rating_IMDB_2 = movies_rating_IMDB[half_len:]
        
        table_1 = tabulate([(i+1, movie[0], movie[1]) for i, movie in enumerate(zip(movies_names_1, movies_rating_IMDB_1))], 
                        headers=["Index", "Movie Name", "Rating IMDB"], 
                        tablefmt="pretty",
                        missingval="--No Rating--")
        table_2 = tabulate([(i+1, movie[0], movie[1]) for i, movie in enumerate(zip(movies_names_2, movies_rating_IMDB_2))], 
                        headers=["Index", "Movie Name", "Rating IMDB"], 
                        tablefmt="pretty",
                        missingval="--No Rating--")
        
        lines_1 = table_1.split('\n')
        lines_2 = table_2.split('\n')
        
        max_len = max(len(lines_1), len(lines_2))
        lines_1 += [''] * (max_len - len(lines_1))
        lines_2 += [''] * (max_len - len(lines_2))

        result = '\n'.join([f'{line1}\t{line2}' for line1, line2 in zip(lines_1, lines_2)])
        print(result)
        

     # movies_names = [movie[0] for movie in movies]
        # movies_rating_IMDB = [movie[1] for movie in movies]
    elif update_seen_flag:
        index_movie_seen = sys.argv.index("--update-seen") + 1
        conn = sqlite3.connect("movies.db")
        cursor = conn.cursor()
        update_seen(cursor=cursor, movie_name=sys.argv[index_movie_seen])
        conn.close()
        
        
    else:
        print("No")
        # column_names = get_column_names("movies")
        
        # conn = sqlite3.connect("movies.db")
        # cursor = conn.cursor()
        # cursor.execute("SELECT * FROM movies")
        
        # rows = cursor.fetchall()
        
        # conn.close()
        
        # df = pd.DataFrame(rows, columns=column_names)
        # df.set_index("id", inplace=True)

        # print(df.head())
        
        

        
if __name__ == "__main__":
    main() 


##### DEBUG FUNCTIONS
def list_tables(database_file):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    
    tables = cursor.fetchall()
    
    conn.close()
    
    table_names = [table[0] for table in tables]
    
    return table_names

def debug():
    database_file = 'movies.db'

    tables = list_tables(database_file)

    print("Tables in the database:")
    for table in tables:
        print(table)