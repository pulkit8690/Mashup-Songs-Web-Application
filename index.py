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

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = '2003pulkit@gmail.com'
app.config['MAIL_PASSWORD'] = 'rkiq uskn hvsm wuok'

mail = Mail(app)

@app.route('/')
def index():
    return render_template('index.html')

def download_video(video_id, output_path):
    yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
    yt.streams.first().download(output_path=output_path)

def convert_to_audio(video_path, duration, output_path):
    clip = VideoFileClip(video_path).subclip(0, duration)
    clip.audio.write_audiofile(output_path)
    clip.close()

def merge_audios(input_dir, output_file):
    audio_files = [os.path.join(input_dir, file) for file in os.listdir(input_dir) if file.endswith(".mp3")]
    combined = AudioSegment.silent(duration=0)
    for file in audio_files:
        combined += AudioSegment.from_mp3(file)
    combined.export(output_file, format="mp3")

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
        temp_dir = tempfile.mkdtemp(prefix='my_app_')

        for i, video in enumerate(search_youtube([singer_name + " songs"])):
            if i == num_videos:
                break
            download_video(video['id'], temp_dir)

        convert_to_audio(temp_dir, audio_duration, output_file)
        merge_audios(temp_dir, output_file)

        msg = Message('Mashup Output', sender='2003pulkit@gmail.com', recipients=[email])
        msg.body = 'Please find attached the output file.'
        with app.open_resource(output_file) as fp:
            msg.attach(output_file, "audio/mp3", fp.read())

        mail.send(msg)

        shutil.rmtree(temp_dir)
        return "Mashup completed successfully. Check your email for the output file."
    except Exception as e:
        traceback.print_exc()
        return "An error occurred: " + str(e)

if __name__ == "__main__":
    app.run(debug=True)
