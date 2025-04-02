from flask import Flask, render_template, redirect, request, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from api.ai import trivia
from api.external import get_weather
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super_secret_key')  # Use env var or fallback
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)  # Hashed
    avatar = db.Column(db.String(150), default='default.png')
    scores = db.relationship('Score', backref='user', lazy=True)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, default=0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('profile'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="Username taken")
        password = generate_password_hash(request.form['password'], method='sha256')
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    scores = Score.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', user=current_user, scores=scores)

# Game Routes with score submission
@app.route('/games/clickmaster', methods=['GET', 'POST'])
@login_required
def clickmaster():
    if request.method == 'POST':
        score = request.json.get('score', 0)
        new_score = Score(user_id=current_user.id, game='clickmaster', score=score)
        db.session.add(new_score)
        db.session.commit()
        return jsonify({'message': 'Score saved'})
    return render_template('games/clickmaster.html')

@app.route('/games/emoji_memory', methods=['GET', 'POST'])
@login_required
def emoji_memory():
    if request.method == 'POST':
        score = request.json.get('score', 0)
        new_score = Score(user_id=current_user.id, game='emoji_memory', score=score)
        db.session.add(new_score)
        db.session.commit()
        return jsonify({'message': 'Score saved'})
    return render_template('games/emoji_memory.html')

@app.route('/games/fliptext')
@login_required
def fliptext():
    return render_template('games/fliptext.html')

@app.route('/games/space_dodger', methods=['GET', 'POST'])
@login_required
def space_dodger():
    if request.method == 'POST':
        score = request.json.get('score', 0)
        new_score = Score(user_id=current_user.id, game='space_dodger', score=score)
        db.session.add(new_score)
        db.session.commit()
        return jsonify({'message': 'Score saved'})
    return render_template('games/space_dodger.html')

@app.route('/games/weather_wizard')
@login_required
def weather_wizard():
    return render_template('games/weather_wizard.html')

@app.route('/games/ai_trivia')
@login_required
def ai_trivia():
    return render_template('games/ai_trivia.html')

@app.route('/api/trivia')
@login_required
def api_trivia():
    data = trivia()
    return jsonify(data)

@app.route('/api/weather')
@login_required
def api_weather():
    city = request.args.get('city', 'London')  # Default city
    data = get_weather(city)
    return jsonify(data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
