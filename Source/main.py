import os.path
from youtubesearchpython import VideosSearch
from tqdm import tqdm;
from pytube import YouTube

import requests

Token = input("Spotify Token: ")
playlist = input("Playlist ID: ")

headers = {'content-type': 'application/json', "Accept": "application/json", "Authorization": "Bearer " + Token}
url = 'https://api.spotify.com/v1/playlists/' + playlist + '/tracks'

r = requests.get(url=url, headers=headers)

result = r.json()
pbar = tqdm(result['items'], desc="Downloading")
# Retrieve Song From Playlist
for x in pbar:
    songName = x['track']['name']
    artistName = []
    fullName = "";
    for y in x['track']['artists']:
        artistName.append(y['name']);
    for z in artistName:
        fullName = songName + " " + z

    videosSearch = VideosSearch(fullName, limit=1)
    videoLink = videosSearch.result()['result'][0]['link']

    yt = YouTube(videoLink)

    ys = yt.streams.filter(only_audio=True).first()

    pbar.set_description("Downloading- " + fullName)

    # Download
    song = ys.download(output_path="./songs/")

    # Convert To MP3
    base, ext = os.path.splitext(song)
    new_file = base + ".mp3"
    os.rename(song, new_file)


print("Download completed")
