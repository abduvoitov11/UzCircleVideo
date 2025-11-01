
from flask import Flask, render_template, request, send_file
import os, moviepy.editor as mp
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    video = request.files['video']
    os.makedirs("static/uploads", exist_ok=True)
    input_path = os.path.join("static/uploads", video.filename)
    video.save(input_path)

    # Dumaloq video (center crop) va 720p
    clip = mp.VideoFileClip(input_path)
    size = min(clip.size)
    clip = clip.crop(x_center=clip.w/2, y_center=clip.h/2, width=size, height=size)
    clip = clip.resize(height=720)
    output_path = os.path.join("static/uploads", f"circle_{datetime.now().strftime('%H%M%S')}.mp4")
    clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
