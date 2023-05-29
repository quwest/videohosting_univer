import sqlite3

from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
import cv2
from DB import DB

UPLOAD_FOLDER = 'static/uploads'
THUMBNAIL_FOLDER = 'static/thumbnails'

app = Flask(__name__)
app.config['DATABASE'] = 'videos.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['THUMBNAIL_FOLDER'] = THUMBNAIL_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mkv'}  # Разрешенные расширения файлов

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', files=files)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        db = DB(app.config['DATABASE'])
        file = request.files['video']
        title = request.form['title']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Generate thumbnail
        thumbnail_filename = generate_thumbnail(filename)
        video = {'filename': filename, 'thumbnail': thumbnail_filename}

        # Save video details to the database
        db.set_new_video_data(video['filename'], video['thumbnail'], title)

        return redirect(url_for('videos'))

    return render_template('upload.html')

def generate_thumbnail(filename):
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], f"{os.path.splitext(filename)[0]}.jpg")

    # Generate thumbnail using OpenCV
    cap = cv2.VideoCapture(video_path)
    success, image = cap.read()
    if success:
        # Resize image if needed
        image = cv2.resize(image, (320, 240))
        cv2.imwrite(thumbnail_path, image)

    cap.release()

    return os.path.basename(thumbnail_path)
@app.route('/video/<filename>')
def video(filename):
    return render_template('video.html', filename=filename)

@app.route('/videos')
def videos():
    db = DB(app.config['DATABASE'])
    videos = db.get_videos_data()

    return render_template('videos.html', videos=videos)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run()