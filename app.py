import os
import zipfile
import smtplib
import re
import time
from email.message import EmailMessage
from flask import Flask, render_template, request
from yt_dlp import YoutubeDL
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import concatenate_audioclips
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# ----------------------------
# Environment Variables
# ----------------------------
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")


# ----------------------------
# Utility Functions
# ----------------------------

def valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)


def clear_folder(folder):
    if os.path.exists(folder):
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except:
                pass


# ----------------------------
# Download Audio Only
# ----------------------------

def download_audios(singer, n):
    os.makedirs("audios", exist_ok=True)
    clear_folder("audios")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audios/%(title)s.%(ext)s',
        'noplaylist': True,
        'ignoreerrors': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch{n}:{singer} songs"])


# ----------------------------
# Create Mashup
# ----------------------------

def create_mashup(duration, output):
    clips = []

    for file in os.listdir("audios"):
        if file.endswith(".mp3"):
            path = os.path.join("audios", file)
            audio_clip = AudioFileClip(path)

            end_time = min(duration, audio_clip.duration)
            clip = audio_clip.subclipped(0, end_time)

            clips.append(clip)

    if not clips:
        raise Exception("No audio files found.")

    final = concatenate_audioclips(clips)
    final.write_audiofile(output)

    final.close()
    for clip in clips:
        clip.close()

    time.sleep(1)


# ----------------------------
# Create Zip
# ----------------------------

def create_zip(mp3_file):
    zip_name = mp3_file.replace(".mp3", ".zip")

    with zipfile.ZipFile(zip_name, 'w') as zipf:
        zipf.write(mp3_file, arcname=os.path.basename(mp3_file))

    return zip_name


# ----------------------------
# Send Email
# ----------------------------

def send_email(receiver_email, zip_file):

    if not SENDER_EMAIL or not APP_PASSWORD:
        raise Exception("Email configuration missing.")

    msg = EmailMessage()
    msg['Subject'] = "Your Mashup File 🎧"
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg.set_content("Hi,\n\nYour mashup is attached.\n\nEnjoy!\n\n- MUSICON")

    with open(zip_file, 'rb') as f:
        msg.add_attachment(
            f.read(),
            maintype='application',
            subtype='zip',
            filename=os.path.basename(zip_file)
        )

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)


# ----------------------------
# Flask Route
# ----------------------------

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            singer = request.form['singer']
            n = int(request.form['videos'])
            duration = int(request.form['duration'])
            email = request.form['email']

            if not valid_email(email):
                return "Invalid Email Address"

            if n <= 10 or duration <= 20:
                return "Videos must be >10 and Duration >20"

            safe_name = singer.replace(" ", "_")
            mashup_name = f"{safe_name}_mashup.mp3"

            download_audios(singer, n)
            create_mashup(duration, mashup_name)

            zip_file = create_zip(mashup_name)
            send_email(email, zip_file)

            # CLEANUP (IMPORTANT FOR STORAGE)
            os.remove(mashup_name)
            os.remove(zip_file)
            clear_folder("audios")

            return "Mashup sent to your email successfully!"

        except Exception as e:
            return f"Error: {str(e)}"

    return render_template("index.html")


# ----------------------------
# Run App
# ----------------------------

if __name__ == "__main__":
    app.run(debug=False)
