import os
import sys
from yt_dlp import YoutubeDL
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import concatenate_audioclips


def download_videos(singer, n):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'videos/%(title)s.%(ext)s',
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }
    os.makedirs("videos", exist_ok=True)
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch{n}:{singer} songs"])


def convert_and_cut(duration):
    clips = []
    for file in os.listdir("videos"):
        if file.endswith(".mp3"):
            path = os.path.join("videos", file)
            audio = AudioFileClip(path)
            end_time = min(duration, audio.duration)
            clip = audio.subclipped(0, end_time)
            clips.append(clip)
    return clips


def merge_audios(clips, output):
    final = concatenate_audioclips(clips)
    final.write_audiofile(output)
    final.close()
    for clip in clips:
        clip.close()


def main():
    if len(sys.argv) != 5:
        print("Usage: python 102317143.py <SingerName> <NumberOfVideos> <AudioDuration> <OutputFileName>")
        return
    singer = sys.argv[1]
    try:
        n = int(sys.argv[2])
        duration = int(sys.argv[3])
    except ValueError:
        print("Number of videos and duration must be integers")
        return
    output = sys.argv[4]
    if n <= 10 or duration <= 20:
        print("Videos must be >10 and duration >20")
        return
    try:
        download_videos(singer, n)
        clips = convert_and_cut(duration)
        merge_audios(clips, output)
        print("Mashup created successfully")
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    main()
