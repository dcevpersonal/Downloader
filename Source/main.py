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
from threading import Thread
from queue import Queue
import time


th_errors = []

num_threads_max = 8


def youtube_music_download():
    name = input("Music Video URL: ")
    m = YouTube(name)
    pbar = tqdm([m.title], desc="Downloading")
    for _ in pbar:
        yd = m.streams.get_highest_resolution()

        pbar.set_description("Downloading- " + m.title)
        song = yd.download(output_path="./YT-Songs/")
        convert_mp4_mp3(song)


def convert_mp4_mp3(song):
    # Convert To MP3
    video_clip = VideoFileClip(song)
    audio_clip = video_clip.audio
    base, ext = os.path.splitext(song)
    new_file = base + ".mp3"
    audio_clip.write_audiofile(new_file, logger=None)

    audio_clip.close()
    video_clip.close()

    return new_file


def youtube_video_download():
    name = input("Video URL: ")
    v = YouTube(name)
    pbar = tqdm([v.title], desc="Downloading")
    for _ in pbar:
        pbar.set_description("Downloading- " + v.title)
        v.streams.get_highest_resolution().download(output_path="./YT-Video/")


def youtube_playlist_download():
    playlist_name = input("Playlist URl: ")
    p = Playlist(playlist_name)

    q = Queue(maxsize=0)
    num_threads = min(num_threads_max, len(p))
    pbar = tqdm(p.videos, desc="Downloading")

    def crawl(que):
        while True:
            time.sleep(0.1)
            try:
                work = que.get_nowait()
                work[0].streams.get_highest_resolution().download(output_path="./YT-Playlists/" + p.title)

            except Exception as es:
                global th_errors
                th_errors.append(es)
                break
            finally:
                pbar.update(1)
                que.task_done()

        return True

    for i in p.videos:
        q.put((i, p.videos))

    create_threads(num_threads, crawl, q)

    q.join()


def create_threads(threads, crawl_f, que_f):
    for y in range(threads):
        worker = Thread(target=crawl_f, args=(que_f,))
        worker.setDaemon(True)
        worker.start()


def spotify_playlist_download():
    # Retrieve Songs From Spotify Playlist
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

    q = Queue(maxsize=0)
    num_threads = min(num_threads_max, len(result_output))
    pbar = tqdm(result_output, desc="Downloading")

    def crawl(que):
        while True:
            time.sleep(0.1)
            try:
                work = que.get_nowait()
                song_name = re.sub(r'[/?.<>|"\\*]', ' ', work[0]['track']['name'])
                artist_name = []
                playlist_artist_name = []
                full_artist_name = ""
                full_playlist_artist_name = ""

                for u in work[0]['track']['artists']:
                    artist_name.append(u['name'])
                for n in work[0]['track']['album']['artists']:
                    playlist_artist_name.append(n['name'])
                for z in artist_name:
                    full_artist_name = full_artist_name + " " + z

                full_name = song_name + "" + full_artist_name

                videos_search = VideosSearch(full_name, limit=1)
                video_link = videos_search.result()['result'][0]['link']

                yt = YouTube(video_link)

                ys = yt.streams.get_highest_resolution()

                # Download
                song = ys.download(output_path="./Spotify-Songs/" + playlist_name)

                new_file = convert_mp4_mp3(song)

                # Add Meta-Data
                audio_cover = "./Spotify-Songs/" + playlist_name + '/' + song_name + ".jpg"

                urllib.request.urlretrieve(work[0]['track']['album']['images'][0]['url'], audio_cover)
                audio_file = eyed3.load(new_file)

                if audio_file.tag is None:
                    audio_file.initTag()

                audio_file.tag.title = song_name
                audio_file.tag.recording_date = Date(int(work[0]['track']['album']['release_date'].split('-')[0]))
                audio_file.tag.album = work[0]['track']['album']['name']
                audio_file.tag.images.set(ImageFrame.FRONT_COVER, open(audio_cover, 'rb').read(), 'image/jpeg')
                audio_file.tag.track_num = work[0]['track']['track_number']
                audio_file.tag.artist = full_artist_name
                for u in playlist_artist_name:
                    full_playlist_artist_name = full_playlist_artist_name + "" + u
                audio_file.tag.album_artist = full_playlist_artist_name

                audio_file.tag.save()
                os.remove(audio_cover)
                os.remove(song)

            except Exception as es:
                global th_errors
                th_errors.append(es)
                break

            finally:
                pbar.update(1)
                que.task_done()

        return True

    for i in result_output:
        q.put((i, result_output))

    create_threads(num_threads, crawl, q)

    q.join()
    print(q.unfinished_tasks)


# Prompt
def main_prompt():
    def clear():
        os.system("cls")

    clear()
    print('\u001b[36m' + r""" 
  ____                      _                 _           
 |  _ \  _____      ___ __ | | ___   __ _  __| | ___ _ __ 
 | | | |/ _ \ \ /\ / / '_ \| |/ _ \ / _` |/ _` |/ _ \ '__|
 | |_| | (_) \ V  V /| | | | | (_) | (_| | (_| |  __/ |   
 |____/ \___/ \_/\_/ |_| |_|_|\___/ \__,_|\__,_|\___|_|  
                                                           """)
    questions = [
        {
            "type": "list",
            "message": "Platform " + "(Threads " + str(num_threads_max) + ")",
            "choices": ["YouTube Video", "YouTube Music", "YouTube Playlist", "Spotify", "Settings"],
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
    elif "Settings" in answer[0]:
        setting_prompt()


def setting_prompt():
    def clear(): os.system("cls")

    clear()
    questions = [

        {"type": "input", "message": "Number Of Threads", "name": "name"},

    ]
    answer = prompt(questions)

    if answer["name"].isdigit():
        global num_threads_max
        num_threads_max = int(answer["name"])

    main_prompt()


main_prompt()
print('\u001b[31m' + "Errors: " + str(len(th_errors)))
print('\u001b[32m' + "Download completed")
print('\u001b[31m' + "Close")
input()
