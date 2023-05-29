import sqlite3

from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
import os
import cv2
from DB import DB
from forms import RegistrationForm, LoginForm

UPLOAD_FOLDER = 'static/uploads'
THUMBNAIL_FOLDER = 'static/thumbnails'

app = Flask(__name__)
app.config['DATABASE'] = 'videos.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['THUMBNAIL_FOLDER'] = THUMBNAIL_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mkv'}
app.config['SECRET_KEY'] = 'your-secret-key'
csrf = CSRFProtect(app)
user_db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, user_db.Model):
    id = user_db.Column(user_db.Integer, primary_key=True)
    username = user_db.Column(user_db.String(100), nullable=False)
    email = user_db.Column(user_db.String(120), unique=True, nullable=False)
    password = user_db.Column(user_db.String(100), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', files=files)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Пользователь с таким email уже существует', 'danger')
            return redirect(url_for('register'))

        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data)
        )

        user_db.session.add(new_user)
        user_db.session.commit()

        flash('Регистрация успешна. Вы можете войти в систему.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not check_password_hash(user.password, form.password.data):
            flash('Неверные email или пароль.', 'danger')
            return redirect(url_for('login'))
        else:
            login_user(user)
            flash('Вход выполнен успешно.', 'success')
            return redirect(url_for('videos'))
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из учетной записи.', 'success')
    return redirect(url_for('index'))

@login_required
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not current_user.is_authenticated:
        flash('Вы не вошли в систему.', 'danger')
        return redirect(url_for('index'))

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
@login_required
@app.route('/video/<filename>')
def video(filename):

    return render_template('video.html', filename=filename)

@app.route('/videos')
def videos():
    db = DB(app.config['DATABASE'])
    videos = db.get_videos_data()

    return render_template('videos.html', videos=videos)


if __name__ == '__main__':
    app.app_context().push()
    user_db.create_all()
    app.run()