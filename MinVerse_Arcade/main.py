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
    coins = db.relationship('PlayerCoins', backref='user', lazy=True)
    clues = db.relationship('DiscoveredClue', backref='user', lazy=True)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, default=0)

# New models for the coin and clue system
class PlayerCoins(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    coins = db.Column(db.Integer, default=0)

class GameClue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_name = db.Column(db.String(50), nullable=False)
    clue_id = db.Column(db.Integer, nullable=False)
    clue_text = db.Column(db.Text, nullable=False)
    __table_args__ = (db.UniqueConstraint('game_name', 'clue_id'),)

class DiscoveredClue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_name = db.Column(db.String(50), nullable=False)
    clue_id = db.Column(db.Integer, nullable=False)
    discovered_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    __table_args__ = (db.UniqueConstraint('user_id', 'game_name', 'clue_id'),)

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
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        # Initialize user's coin balance
        new_coins = PlayerCoins(user_id=new_user.id, coins=0)
        db.session.add(new_coins)
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
    # Get user's highest scores for each game
    scores = db.session.query(Score.game, db.func.max(Score.score).label('score')) \
                      .filter_by(user_id=current_user.id) \
                      .group_by(Score.game) \
                      .all()
    
    # Get total games played count
    games_played = Score.query.filter_by(user_id=current_user.id).count()
    
    # Get user's coins
    player_coins = PlayerCoins.query.filter_by(user_id=current_user.id).first()
    coins = player_coins.coins if player_coins else 0
    
    # Get user's discovered clues with their text
    discovered_clues = db.session.query(DiscoveredClue, GameClue) \
                               .join(GameClue, 
                                    (DiscoveredClue.game_name == GameClue.game_name) & 
                                    (DiscoveredClue.clue_id == GameClue.clue_id)) \
                               .filter(DiscoveredClue.user_id == current_user.id) \
                               .all()
    
    clues = [{"game_name": clue.DiscoveredClue.game_name, 
             "clue_text": clue.GameClue.clue_text} 
             for clue in discovered_clues]
    
    return render_template('profile.html', 
                          user=current_user, 
                          scores=scores, 
                          games_played=games_played,
                          coins=coins,
                          clues=clues)

# Game Routes with score submission and clue discovery
@app.route('/games/clickmaster', methods=['GET', 'POST'])
@login_required
def clickmaster():
    if request.method == 'POST':
        data = request.json
        score = data.get('score', 0)
        
        # Save the score
        new_score = Score(user_id=current_user.id, game='clickmaster', score=score)
        db.session.add(new_score)
        
        # Initialize response data
        response_data = {'message': 'Score saved'}
        
        # Check if the score is exactly 42 (our threshold for the clue)
        if score == 42:
            # Award 3 coins
            player_coins = PlayerCoins.query.filter_by(user_id=current_user.id).first()
            if player_coins:
                player_coins.coins += 3
            else:
                player_coins = PlayerCoins(user_id=current_user.id, coins=3)
                db.session.add(player_coins)
            
            # Check if the clue exists, create it if not
            clue = GameClue.query.filter_by(game_name='clickmaster', clue_id=1).first()
            if not clue:
                clue = GameClue(
                    game_name='clickmaster',
                    clue_id=1,
                    clue_text="The key to defeating NEXUS lies in patterns. Remember: 42 is the answer to everything."
                )
                db.session.add(clue)
            
            # Mark clue as discovered if not already
            discovered = DiscoveredClue.query.filter_by(
                user_id=current_user.id,
                game_name='clickmaster',
                clue_id=1
            ).first()
            
            if not discovered:
                discovered = DiscoveredClue(
                    user_id=current_user.id,
                    game_name='clickmaster',
                    clue_id=1
                )
                db.session.add(discovered)
            
            # Add clue info to response
            response_data.update({
                'show_clue': True,
                'clue': clue.clue_text,
                'earned_coins': 3
            })
        
        db.session.commit()
        return jsonify(response_data)
    
    return render_template('games/clickmaster.html')

@app.route('/user/coins')
@login_required
def get_user_coins():
    player_coins = PlayerCoins.query.filter_by(user_id=current_user.id).first()
    coins = player_coins.coins if player_coins else 0
    return jsonify({'coins': coins})

@app.route('/user/clues')
@login_required
def get_user_clues():
    discovered_clues = db.session.query(DiscoveredClue, GameClue) \
                              .join(GameClue, 
                                   (DiscoveredClue.game_name == GameClue.game_name) & 
                                   (DiscoveredClue.clue_id == GameClue.clue_id)) \
                              .filter(DiscoveredClue.user_id == current_user.id) \
                              .all()
    
    clues = [{"game": clue.DiscoveredClue.game_name, "text": clue.GameClue.clue_text} 
             for clue in discovered_clues]
    
    return jsonify({'clues': clues})

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

# Initialize game clues at startup
def init_game_clues():
    # Define the initial clues for each game
    initial_clues = [
        ('clickmaster', 1, "The key to defeating NEXUS lies in patterns. Remember: 42 is the answer to everything."),
        ('fliptext', 1, "NEXUS fears reversed logic. What looks normal may need to be flipped."),
        ('emoji_memory', 1, "NEXUS has a weak memory for faces. Show it the same pattern twice to confuse it."),
        ('space_dodger', 1, "NEXUS cannot predict random movements. Chaos is your ally."),
        ('weather_wizard', 1, "NEXUS overheats easily. Cold climates weaken its defenses."),
        ('ai_trivia', 1, "Knowledge is power. NEXUS has a blind spot about its own creation.")
    ]
    
    # Add clues if they don't exist
    for game_name, clue_id, clue_text in initial_clues:
        clue = GameClue.query.filter_by(game_name=game_name, clue_id=clue_id).first()
        if not clue:
            clue = GameClue(game_name=game_name, clue_id=clue_id, clue_text=clue_text)
            db.session.add(clue)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_game_clues()  # Initialize game clues
    app.run(debug=True)