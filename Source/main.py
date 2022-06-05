import os.path

import eyed3
from youtubesearchpython import VideosSearch
from tqdm import tqdm
from pytube import YouTube, Playlist
import requests
from requests.auth import HTTPBasicAuth
from InquirerPy import prompt
from moviepy.video.io.VideoFileClip import VideoFileClip
import re
import urllib.request
from eyed3.id3.frames import ImageFrame
from eyed3.core import Date


def youtube_music_download():
    name = input("Music Video URL: ")
    m = YouTube(name)
    pbar = tqdm([m.title], desc="Downloading")
    for _ in pbar:
        yd = m.streams.get_highest_resolution()

        pbar.set_description("Downloading- " + m.title)
        song = yd.download(output_path="./YT-Songs/")
        convert_mp4_mp3(song)

    print('\u001b[32m' + "Download completed")


def convert_mp4_mp3(song):
    # Convert To MP3
    video_clip = VideoFileClip(song)
    audio_clip = video_clip.audio
    base, ext = os.path.splitext(song)
    new_file = base + ".mp3"
    audio_clip.write_audiofile(new_file, logger=None)
    audio_clip.close()
    video_clip.close()
    os.remove(song)

    return new_file


def youtube_video_download():
    name = input("Video URL: ")
    v = YouTube(name)
    pbar = tqdm([v.title], desc="Downloading")
    for _ in pbar:
        pbar.set_description("Downloading- " + v.title)
        v.streams.get_highest_resolution().download(output_path="./YT-Video/")

    print('\u001b[32m' + "Download completed")


def youtube_playlist_download():
    playlist_name = input("Playlist URl: ")
    p = Playlist(playlist_name)
    pbar = tqdm(p.videos, desc="Downloading")

    for x in pbar:
        pbar.set_description("Downloading- " + x.title)
        x.streams.get_highest_resolution().download(output_path="./YT-Playlists/" + p.title)

    print('\u001b[32m' + "Download completed")


def spotify_playlist_download():
    client_id = os.environ.get("SPOTIFY_ID")
    client_secret = os.environ.get("SPOTIFY_SECRET")

    token_post = requests.post("https://accounts.spotify.com/api/token", data="grant_type=client_credentials",
                               headers={'content-type': 'application/x-www-form-urlencoded'},
                               auth=HTTPBasicAuth(client_id, client_secret))
    token = token_post.json()["access_token"]

    playlist = input("Playlist ID: ")
    playlist = re.sub('https://open.spotify.com/playlist/', '', playlist)
    playlist = re.split('\\?', playlist)[0]

    headers = {'content-type': 'application/json', "Accept": "application/json", "Authorization": "Bearer " + token}
    url = 'https://api.spotify.com/v1/playlists/' + playlist + "/tracks?limit=100&offset=0"

    result = requests.get(url=url, headers=headers).json()
    playlist_name = requests.get(url='https://api.spotify.com/v1/playlists/' + playlist, headers=headers).json()['name']
    offset = 0
    result_output = []

    while len(result['items']) != 0:
        for x in result['items']:
            result_output.append(x)
        offset += 100
        url = 'https://api.spotify.com/v1/playlists/' + playlist + "/tracks?limit=100&offset=" + str(offset)
        result = requests.get(url=url, headers=headers).json()

    pbar = tqdm(result_output, desc="Downloading")

    # Retrieve Song From Playlist
    for x in pbar:
        song_name = x['track']['name']
        artist_name = []
        playlist_artist_name = []
        full_artist_name = ""
        full_playlist_artist_name = ""

        for y in x['track']['artists']:
            artist_name.append(y['name'])
        for n in x['track']['album']['artists']:
            playlist_artist_name.append(n['name'])
        for z in artist_name:
            full_artist_name = full_artist_name + " " + z

        full_name = song_name + "" + full_artist_name

        videos_search = VideosSearch(full_name, limit=1)
        video_link = videos_search.result()['result'][0]['link']

        yt = YouTube(video_link)

        ys = yt.streams.get_highest_resolution()

        pbar.set_description("Downloading- " + full_name)

        # Download
        song = ys.download(output_path="./Spotify-Songs/" + playlist_name)

        new_file = convert_mp4_mp3(song)

        # Add Meta-Data
        audio_cover = "./Spotify-Songs/" + playlist_name + '/' + song_name + ".jpg"

        urllib.request.urlretrieve(x['track']['album']['images'][0]['url'], audio_cover)
        audio_file = eyed3.load(new_file)

        if audio_file.tag is None:
            audio_file.initTag()

        audio_file.tag.title = song_name
        audio_file.tag.recording_date = Date(int(x['track']['album']['release_date'].split('-')[0]))
        audio_file.tag.album = x['track']['album']['name']
        audio_file.tag.images.set(ImageFrame.FRONT_COVER, open(audio_cover, 'rb').read(), 'image/jpeg')
        audio_file.tag.track_num = x['track']['track_number']
        audio_file.tag.artist = full_artist_name
        for u in playlist_artist_name:
            full_playlist_artist_name = full_playlist_artist_name + "" + u
        audio_file.tag.album_artist = full_playlist_artist_name

        audio_file.tag.save()
        os.remove(audio_cover)
    print('\u001b[32m' + "Download completed")


# Prompt
questions = [
    {
        "type": "list",
        "message": "Platform",
        "choices": ["YouTube Video", "YouTube Music", "YouTube Playlist", "Spotify"],
    },
]

answer = prompt(questions)

if "Spotify" in answer[0]:
    spotify_playlist_download()
elif "YouTube Video" in answer[0]:
    youtube_video_download()
elif "YouTube Music" in answer[0]:
    youtube_music_download()
elif "YouTube Playlist" in answer[0]:
    youtube_playlist_download()
print('\u001b[31m' + "Close")
input()
