import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from time import sleep
from random import randint
import json

#function to format runtime
def clean_runtime(runtime):
    hours = 0
    if 'h' in runtime:
        hours = int(runtime.split('h')[0])
    minutes = 0
    if 'm' in runtime:
        minutes = int(runtime.split('m')[0].split('h')[-1])
    return hours * 60 + minutes

#function to format gross
def clean_gross(gross):
    clean = gross.replace('$','').replace(',','')
    return int(clean)


top250_url = 'https://www.imdb.com/chart/top/?ref_=nv_mv_250'

page = requests.get(top250_url)
print('request was sent to: {} -- with respose code = {}'.format(top250_url, page.status_code))

soup = BeautifulSoup(page.content, 'html.parser')
movies_list = soup.find(class_= 'lister-list')
movies = movies_list.select('.titleColumn>a')


scraped_movies = []
scraped_genres = []
scraped_person = []
scraped_crew =[]
scraped_cast = []


for num in tqdm (range (len(movies)), desc="Loading..."):
    identifier = movies[num].get('href')

    scraped_movie = {}
    
    
    url = 'https://www.imdb.com{}'.format(identifier)
    movie_page = requests.get(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US,en;q=0.9'})
    movie_page.status_code
    movie_soup = BeautifulSoup(movie_page.content, 'html.parser')
    

    section1 = movie_soup.find(class_='ipc-inline-list ipc-inline-list--show-dividers sc-afe43def-4 kdXikI baseAlt').find_all('li')
    section2 = movie_soup.find(class_='sc-52d569c6-3 jBXsRT')

    #movie title and id:
    movie_id = identifier.split('tt')[1][:-1]
    scraped_movie['id'] = movie_id


    scraped_movie['title'] = movie_soup.find(class_='sc-afe43def-1 fDTGTb').text

    # -- data from section 1 --



    if len(section1) == 3:
        scraped_movie['year'] = int(section1[0].text)
        scraped_movie['runtime'] = clean_runtime(section1[2].text)

        if section1[1].text == 'Not Rated':
            scraped_movie['parental_guide'] = 'Unrated'
        else:
            scraped_movie['parental_guide'] = section1[1].text
    else:
        scraped_movie['year'] = int(section1[0].text)
        scraped_movie['runtime'] = clean_runtime(section1[1].text)
        scraped_movie['parental_guide'] = 'Unrated'

    #getting box office "Gross US & Canada"
    try:
        us_ca_gross = movie_soup.find('li', {'data-testid': 'title-boxoffice-grossdomestic'}).find('li').text
        scraped_movie['gross_us_canada'] = clean_gross(us_ca_gross)
    except AttributeError:
        scraped_movie['gross_us_canada'] = None
    
    scraped_movies.append(scraped_movie)



    # -- data from section 2 --

    #getting genres:
    for gen in movie_soup.find('div', {'data-testid' :'genres'}).find_all('a'):
        movie_genres = {}
        movie_genres['movie_id'] = movie_id
        movie_genres['genre'] = gen.text
        scraped_genres.append(movie_genres)

    


    #getting directors:
    for director in section2.find_all(class_= 'ipc-metadata-list__item')[0].find_all('li'):
        person = {}
        crew = {}
        direc_name = director.find('a').text
        direc_id = director.find('a').get('href').split('nm')[1].split('/')[0]
        
        crew['movie_id'] = movie_id
        crew['person_id'] = direc_id
        crew['role'] = 'Director'
        scraped_crew.append(crew)

        person['id'] = direc_id
        person['name'] = direc_name
        if not any(individual['id'] == person['id'] for individual in scraped_person):
            scraped_person.append(person)
        

    


    #getting writers:
    for writer in section2.find_all(class_= 'ipc-metadata-list__item')[1].find_all('li'):
        person = {}
        crew = {}
        wrt_name = writer.find('a').text
        wrt_id = writer.find('a').get('href').split('nm')[1].split('/')[0]

        crew['movie_id'] = movie_id
        crew['person_id'] = wrt_id
        crew['role'] = 'Writer'
        scraped_crew.append(crew)

        
        person['id'] = wrt_id
        person['name'] = wrt_name
        if not any(individual['id'] == person['id'] for individual in scraped_person):
            scraped_person.append(person)
        


    
    #getting stars:
    for star in section2.find_all(class_= 'ipc-metadata-list__item')[2].find_all('li'):
        person = {}
        cast = {}
        satr_name = star.find('a').text
        star_id = star.find('a').get('href').split('nm')[1].split('/')[0]

        cast['movie_id'] = movie_id
        cast['person_id'] = star_id
        scraped_cast.append(cast)

        person['id'] = star_id
        person['name'] = satr_name
        if not any(individual['id'] == person['id'] for individual in scraped_person):
            scraped_person.append(person)
    

    # Sleep for a random time to avoid being blocked
    time_milliseconds = randint(500, 2000)
    time_sec = 0.001 * time_milliseconds
    sleep(time_sec)
    

print('--- Done! ---')


scraped_data = [scraped_movies, scraped_genres, scraped_person, scraped_crew, scraped_cast]

with open("IMDb_250.json", "w") as file:
    json.dump(scraped_data, file)