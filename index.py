from flask import Flask, render_template, request, redirect, url_for
import os
import sys
import shutil
from pytube import YouTube
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from fast_youtube_search import search_youtube
from flask_mail import Mail, Message

app = Flask(__name__)

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = '2003pulkit@gmail.com'  # Your Gmail username
app.config['MAIL_PASSWORD'] = 'rkiq uskn hvsm wuok'  # Your Gmail password

mail = Mail(app)

def download_videos(singer_name, num_videos):
    print(f"Downloading {num_videos} videos of {singer_name}...")
    try:
        results = search_youtube([singer_name + " songs"])

        for i, video in enumerate(results):
            if i == num_videos:
                break
            yt = YouTube(f"https://www.youtube.com/watch?v={video['id']}")
            yt.streams.first().download(output_path="temp", filename=f"video_{i+1}.mp4")  # Ensure .mp4 extension
        print("Videos downloaded successfully.")
    except Exception as e:
        print("Error downloading videos:", str(e))
        sys.exit(1)


        
def convert_to_audio(duration):
    print("Converting videos to audio...")
    try:
        for filename in os.listdir("temp"):
            if filename.endswith(".mp4"):
                video_path = os.path.join("temp", filename)
                audio_path = os.path.join("temp", f"{os.path.splitext(filename)[0]}.mp3")
                clip = VideoFileClip(video_path)
                clip = clip.subclip(0, duration)  # Take first 'duration' seconds of video
                audio = clip.audio
                audio.write_audiofile(audio_path)
                clip.close()  # Close the video clip to release resources
        print("Conversion to audio completed.")
    except Exception as e:
        print("Error converting to audio:", str(e))
        sys.exit(1)



def merge_audios(output_file):
    print("Merging audio files...")
    try:
        audio_files = [file for file in os.listdir("temp") if file.endswith(".mp3")]
        combined = None
        for file in audio_files:
            sound = AudioSegment.from_mp3(os.path.join("temp", file))
            if combined is None:
                combined = sound
            else:
                combined += sound
        
        if combined:
            combined.export(output_file, format="mp3")
            print("Audio files merged successfully.")
        else:
            print("No audio files found to merge.")
            sys.exit(1)
    except Exception as e:
        print("Error merging audio files:", str(e))
        sys.exit(1)

@app.route('/')
def index():
    return render_template('index.html')

import traceback
@app.route('/submit', methods=['POST'])
def submit():
    try:
        singer_name = request.form['singer_name']
        num_videos = int(request.form['num_videos'])
        audio_duration = int(request.form['audio_duration'])
        email = request.form['email']

        if num_videos <= 0 or audio_duration <= 0:
            return "Number of videos and audio duration must be positive integers."

        output_file = "output.mp3"

        os.makedirs("temp", exist_ok=True)
        download_videos(singer_name, num_videos)
        convert_to_audio(audio_duration)
        merge_audios(output_file)
        
        # Send email
        msg = Message('Mashup Output', sender='2003pulkit@gmail.com', recipients=[email])
        msg.body = 'Please find attached the output file.'
        with app.open_resource(output_file) as fp:
            msg.attach(output_file, "audio/mp3", fp.read())

        mail.send(msg)

        shutil.rmtree("temp")

        return "Mashup completed successfully. Check your email for the output file."
    except Exception as e:
        # Log the error message along with the traceback
        traceback.print_exc()  # Print the traceback to console
        return "An error occurred: " + str(e)

if __name__ == "__main__":
    app.run(debug=True)
 