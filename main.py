import requests
from bs4 import BeautifulSoup
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv('.env')

CLIENT_ID: str = os.getenv("CLIENT_ID")
CLIENT_SECRET: str = os.getenv("CLIENT_SECRET")
REDIRECT_URI: str = os.getenv("REDIRECT_URI")
SCOPE: str = os.getenv('SCOPE')
SPOTIFY_URL: str = "http://open.spotify.com/"

try:
    date_str = input("Which year do you want to travel to? Type the date in this format YYYY-MM-DD: ")
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%Y-%m-%d")
    year = formatted_date.split("-")[0]
except ValueError as value_error:
    print(f"{value_error}")

else:
    url = f"https://www.billboard.com/charts/hot-100/{formatted_date}"

    response = requests.get(url=url)
    bd_data = response.text

    soap = BeautifulSoup(bd_data, "html.parser")
    hit_titles = soap.find_all(name="h3", class_="a-no-trucate")
    hit_labels = soap.find_all(name="span", class_="a-no-trucate")

    hits_title_list: list = [hit_title.getText().strip() for hit_title in hit_titles]
    sliced_hits_title_list: list = hits_title_list[:10]
    hits_label_list: list = [hit_label.getText().strip() for hit_label in hit_labels]
    sliced_hits_label_list: list = hits_label_list[:10]

    with open("top_hits.txt", "w", encoding="utf-8") as data:
        for titles, labels in zip(sliced_hits_title_list, sliced_hits_label_list):
            data.write(f"{titles}\n")


def access_token():
    sp_oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=".cache",
        show_dialog=True
    )
    token_info = sp_oauth.get_cached_token()

    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        print(auth_url)
        token_response = input('Paste the above link into your browser, then paste the redirect url here: ')
        code = sp_oauth.parse_response_code(token_response)
        token_info = sp_oauth.get_access_token(code)

    return token_info['access_token']


sp = spotipy.Spotify(auth=access_token())
user_info = sp.current_user()
user_id: str = user_info["id"]

with open("top_hits.txt", "r") as hits_data:
    hits_list = hits_data.readlines()
name: str = input("Enter name of person: ").title()
with open("top_10_hits.txt", "w") as top_10_hit:
    top_10_hit.write(f"\nTop Hits for {name}\n")
    spotify_uri_list = []
    for index, hit in enumerate(hits_list):
        clean_hits: str = hit.strip()
        try:
            search_for_hits = sp.search(q=f'track:{clean_hits} year:{year}', type='track')
            spotify_uri = search_for_hits["tracks"]["items"][0]['uri']
            top_10_hit.write(f"Hit name: {clean_hits}, Spotify uri: {spotify_uri}\n")
            spotify_uri_list.append(spotify_uri)
        except IndexError as err:
            print(f"{hit} doesn't exist in Spotify. Skipped.")


playlist = sp.user_playlist_create(user=user_id, name=f"{formatted_date} Billboard 100", public=False)
ad_hits = sp.playlist_add_items(playlist_id=playlist["id"], items=spotify_uri_list)
