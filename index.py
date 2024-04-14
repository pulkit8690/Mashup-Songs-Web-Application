import os
import sys
import shutil
from pytube import YouTube
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from fast_youtube_search import search_youtube
from flask_mail import Mail, Message
import tempfile
from flask import Flask, render_template,request
import traceback

# Flask app setup
app = Flask(__name__)

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = ''  # Your Gmail username
app.config['MAIL_PASSWORD'] = ''  # Your Gmail password

mail = Mail(app)

# Create a temporary directory in /tmp
temp_dir = tempfile.mkdtemp(prefix='my_app_')

# Define functions to download videos, convert to audio, and merge audio

def download_videos(singer_name, num_videos):
    print(f"Downloading {num_videos} videos of {singer_name}...")
    try:
        results = search_youtube([singer_name + " songs"])

        for i, video in enumerate(results):
            if i == num_videos:
                break
            yt = YouTube(f"https://www.youtube.com/watch?v={video['id']}")
            yt.streams.first().download(output_path=temp_dir, filename=f"video_{i+1}.mp4")  # Ensure .mp4 extension
        print("Videos downloaded successfully.")
    except Exception as e:
        print("Error downloading videos:", str(e))
        sys.exit(1)

def convert_to_audio(duration):
    print("Converting videos to audio...")
    try:
        for filename in os.listdir(temp_dir):
            if filename.endswith(".mp4"):
                video_path = os.path.join(temp_dir, filename)
                audio_path = os.path.join(temp_dir, f"{os.path.splitext(filename)[0]}.mp3")
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
        audio_files = [file for file in os.listdir(temp_dir) if file.endswith(".mp3")]
        combined = None
        for file in audio_files:
            sound = AudioSegment.from_mp3(os.path.join(temp_dir, file))
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

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

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

        download_videos(singer_name, num_videos)
        convert_to_audio(audio_duration)
        merge_audios(output_file)
        
        # Send email
        msg = Message('Mashup Output', sender='2003pulkit@gmail.com', recipients=[email])
        msg.body = 'Please find attached the output file.'
        with app.open_resource(output_file) as fp:
            msg.attach(output_file, "audio/mp3", fp.read())

        mail.send(msg)

        shutil.rmtree(temp_dir)  # Cleanup the temporary directory

        return "Mashup completed successfully. Check your email for the output file."
    except Exception as e:
        traceback.print_exc()  # Print the traceback to console
        return "An error occurred: " + str(e)

if __name__ == "__main__":
    app.run(debug=True)
