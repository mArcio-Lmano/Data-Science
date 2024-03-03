import requests
import sqlite3
import argparse
import json
import os

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
        self.rating_IMDB = rating_IMDB
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
        console_string = f"""Name: {self.name}
    Link:         {self.link}
    IMBD Rating:  {self.rating_IMDB}
    MPPA Rating:  {self.rating_MPPA}
    Year:         {self.year},
    Released yet: {self.released}
    Duration:     {self.duration}
    Added to the personal database: {self.add_to_db_date}
        Genres:   {self.genres}
        Director: {self.director}
        Language: {self.language}
        Seen:     {self.seen}
        """
        print(console_string)
        return None



def scrapeImdb(url, headers) -> BeautifulSoup:
    try:
        response = requests.get(url=url, headers=headers)
        response.raise_for_status()  
        soup = BeautifulSoup(response.text, "html.parser")
        return soup
    except requests.RequestException as e:
        print("An error occurred while fetching data from IMDb:", e)
        return None

def getPopularMovies() -> list:
    url = "https://www.imdb.com/chart/moviemeter/?ref_=nv_mv_mpm"
    with open("headers.json", "r") as f:
        headers = json.load(f)
   
    soup = scrapeImdb(url=url, headers=headers)
    if soup:
        movies_html_list = soup.find_all("li", class_="ipc-metadata-list-summary-item sc-1364e729-0 caNpAE cli-parent")
    else:
        return None
    
    movies = []
    for movie_html in movies_html_list:
        a_tag = movie_html.find("a", class_="ipc-title-link-wrapper")
        movie_name = a_tag.h3.text
        link_aux = a_tag["href"].split("/")
        movie_link = "https://www.imdb.com/title/" + link_aux[2]
        
        movie_rating_IMDB = movie_html.find("span", class_="ipc-rating-star ipc-rating-star--base ipc-rating-star--imdb ratingGroup--imdb-rating")
        movie_rating_IMDB = movie_rating_IMDB.text if movie_rating_IMDB else None
            
        movie_infos = movie_html.find_all("span", class_="sc-be6f1408-8 fcCUPU cli-title-metadata-item")
        movies_infos_text = [info.text for info in movie_infos]
        movies_infos_text = [movies_infos_text[i] if i<len(movies_infos_text) else None for i in range(3)]

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



def createDataBase(movies):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()

    createMoviesTable(cursor)

    for movie in movies:
        insertMovie(cursor, movie)

    conn.commit()
    conn.close()
    return 
        
def createMoviesTable(cursor):
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
        
def insertMovie(cursor, movie):
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
        
def updateSeenEntry(cursor, movie_name):
    cursor.execute("SELECT seen FROM movies WHERE name = ?", (movie_name,))
    result = cursor.fetchone()
    if result and result[0] is not None:
        user_input = input(f"You already seen this movie in {result[0]}. Do you want to update it anyway? [Y/n]: ")
        if user_input.lower() != 'y':
            print("Update aborted.")
            return
        
    seen_date = datetime.now().date()
    cursor.execute("UPDATE movies SET seen = ? WHERE name = ?", (seen_date, movie_name))
    
    cursor.execute("SELECT * FROM movies WHERE name = ?", (movie_name,))
    
    movie_info = cursor.fetchone()
    if movie_info:
        movie = Movie(name=movie_info[1],
                      link=movie_info[2],
                      rating_IMDB=movie_info[3],
                      rating_MPPA=movie_info[4],
                      year=movie_info[5],
                      duration=movie_info[6],
                      genres=movie_info[7],
                      director=movie_info[8],
                      language=movie_info[9],
                      actors=movie_info[10], 
                      seen=seen_date
                      )
    
        movie.printMovie()
  
        

def createNewDb():
    database_found = os.path.exists("movies.db")
    if database_found:
        user_flag = input("A database file already exists. Are you sure you want to continue and overwrite it? [Y/n]: ")
        
    if not database_found or user_flag.lower() == 'y':
        movies = getPopularMovies()
        if database_found: 
            os.remove("movies.db")
            
        if movies:
            createDataBase(movies)
        else:
            print("Failed to fetch movies from IMDb.")
    else:
        print("Database creation aborted.")
        
def listMovies(list_type):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    
    if list_type == "all":
        cursor.execute("SELECT name, rating_IMDB FROM movies")
        movies = cursor.fetchall()
    elif list_type == "seen":
        cursor.execute("SELECT name, rating_IMDB FROM movies WHERE seen IS NOT NULL")
        movies = cursor.fetchall()
    else:
        cursor.execute("SELECT name, rating_IMDB FROM movies WHERE seen IS NULL")
        movies = cursor.fetchall()
        
    conn.close()
    
    half_len = (len(movies) + 1) // 2 
    movies_1 = movies[:half_len]
    movies_2 = movies[half_len:]
    
    print(len(movies))
    if len(movies) == 1:
        movies_1 = movies
        movies_2 = []
    
    table_1 = tabulate([(i+1, movie[0], movie[1]) for i, movie in enumerate(movies_1)], 
                    headers=["Index", "Movie Name", "Rating IMDB"], 
                    tablefmt="pretty",
                    missingval="-- No Rating --")
    
    table_2 = tabulate([(i+1, movie[0], movie[1]) for i, movie in enumerate(movies_2, start=half_len)], 
                    headers=["Index", "Movie Name", "Rating IMDB"], 
                    tablefmt="pretty",
                    missingval="-- No Rating --") if len(movies) != 1 else ""

    lines_1 = table_1.split('\n')
    lines_2 = table_2.split('\n')

    max_len = max(len(lines_1), len(lines_2))

    # Extend the shorter table to match the length of the longer one
    lines_1.extend([''] * (max_len - len(lines_1)))
    lines_2.extend([''] * (max_len - len(lines_2)))

    # Combine the lines from both tables
    result = '\n'.join([f'{line1}\t{line2}' for line1, line2 in zip(lines_1, lines_2)])

    print(f"MOVIES: {list_type}")
    print(result)
        
def updateSeen(movie_name):
    print(movie_name)
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    updateSeenEntry(cursor=cursor, movie_name=movie_name)
    conn.commit()
    conn.close()        
    
    

def main():
    parser = argparse.ArgumentParser(description="IMDb Movie Management System")
    parser.add_argument("--new", action="store_true", help="Create a new database")
    parser.add_argument("--list-movies", choices=["all", "seen", "not-seen"], help="List movies by type")
    parser.add_argument("--update-seen", metavar="MOVIE_NAME", help="Update seen status of a movie")
    
    args = parser.parse_args()

    if args.new:
        createNewDb()
    elif args.list_movies:
        listMovies(args.list_movies)
    elif args.update_seen:
        updateSeen(args.update_seen)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 
