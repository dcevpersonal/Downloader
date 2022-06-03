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

def YouTubeMusicDownload():
    name = input("Music Video URL: ")
    m = YouTube(name)
    pbar = tqdm([m.title], desc="Downloading")
    for x in pbar:
        yd = m.streams.get_highest_resolution()

        pbar.set_description("Downloading- " + m.title)
        song = yd.download(output_path="./ytsongs/")

        # Convert To MP3
        videoClip = VideoFileClip(song)
        audioClip = videoClip.audio
        base, ext = os.path.splitext(song)
        new_file = base + ".mp3"
        audioClip.write_audiofile(new_file, logger=None)
        audioClip.close()
        videoClip.close()
        os.remove(song)

    print('\u001b[32m' + "Download completed")


def YouTubeVideoDownload():
    name = input("Video URL: ")
    v = YouTube(name)
    pbar = tqdm([v.title], desc="Downloading")
    for x in pbar:

        pbar.set_description("Downloading- " + v.title)
        v.streams.get_highest_resolution().download(output_path="./ytvideo/")



    print('\u001b[32m' + "Download completed")


def YouTubePlaylistDownload():
    playlistName = input("Playlist URl: ")
    p = Playlist(playlistName)
    pbar = tqdm(p.videos, desc="Downloading")

    for x in pbar:

        pbar.set_description("Downloading- " + x.title)
        x.streams.get_highest_resolution().download(output_path="./ytplaylists/" + p.title )

    print('\u001b[32m' + "Download completed")


def SpotifyPlaylistDownload():
    ClientId = os.environ.get("SPOTIFYID")
    ClientSecret = os.environ.get("SPOTIFYSECRET")

    tokenPost = requests.post("https://accounts.spotify.com/api/token", data="grant_type=client_credentials", headers={'content-type': 'application/x-www-form-urlencoded'}, auth=HTTPBasicAuth(ClientId,ClientSecret))
    Token = tokenPost.json()["access_token"]

    playlist = input("Playlist ID: ")
    playlist = re.sub('https://open.spotify.com/playlist/','',playlist)
    playlist = re.split('\?', playlist)[0]

    headers = {'content-type': 'application/json', "Accept": "application/json", "Authorization": "Bearer " + Token}
    url = 'https://api.spotify.com/v1/playlists/' + playlist

    r = requests.get(url=url, headers=headers)

    result = r.json()
    playlistName = result['name']
    pbar = tqdm(result['tracks']['items'], desc="Downloading")

    # Retrieve Song From Playlist
    for x in pbar:
        songName = x['track']['name']
        artistName = []
        playlistArtistName = []
        fullName = "";
        fullArtistName = "";
        fullPlaylistArtistName = ""


        for y in x['track']['artists']:
            artistName.append(y['name']);
        for n in x['track']['album']['artists']:
            playlistArtistName.append(n['name'])
        for z in artistName:
            fullArtistName = fullArtistName + " " + z

        fullName = songName + "" + fullArtistName

        videosSearch = VideosSearch(fullName, limit=1)
        videoLink = videosSearch.result()['result'][0]['link']

        yt = YouTube(videoLink)

        ys = yt.streams.get_highest_resolution()

        pbar.set_description("Downloading- " + fullName)

        # Download
        song = ys.download(output_path="./spotifysongs/" + playlistName)

        # Convert To MP3
        videoClip = VideoFileClip(song)
        audioClip = videoClip.audio
        base, ext = os.path.splitext(song)
        new_file = base + ".mp3"
        audioClip.write_audiofile(new_file, logger=None)
        audioClip.close()
        videoClip.close()
        os.remove(song)

        #Add Meta-Data
        audioCover = "./spotifysongs/" + playlistName + '/' + songName + ".jpg"

        urllib.request.urlretrieve(x['track']['album']['images'][0]['url'],audioCover)
        audioFile = eyed3.load(new_file)

        if audioFile.tag == None:
            audioFile.initTag()

        audioFile.tag.title = songName
        audioFile.tag.recording_date = Date(int(x['track']['album']['release_date'].split('-')[0]))
        audioFile.tag.album = x['track']['album']['name']
        audioFile.tag.images.set(ImageFrame.FRONT_COVER, open(audioCover, 'rb').read(), 'image/jpeg');
        audioFile.tag.track_num = x['track']['track_number']
        audioFile.tag.artist = fullArtistName
        for u in playlistArtistName:
            fullPlaylistArtistName = fullPlaylistArtistName + "" + u
        audioFile.tag.album_artist = fullPlaylistArtistName




        audioFile.tag.save()
        os.remove(audioCover)
    print('\u001b[32m' + "Download completed")


# Prompt
questions = [
    {
        "type": "list",
        "message": "Platform",
        "choices": ["YouTube Video", "YouTube Music", "YouTube Playlist", "Spotify"],
    },
]

result = prompt(questions)


if "Spotify" in result[0]:
    SpotifyPlaylistDownload()
elif "YouTube Video" in result[0]:
    YouTubeVideoDownload()
elif "YouTube Music" in result[0]:
    YouTubeMusicDownload()
elif "YouTube Playlist" in result[0]:
    YouTubePlaylistDownload()
print('\u001b[31m' + "Close")
input()
