from flask import Flask, render_template, redirect, request, url_for, jsonify, abort, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from api.ai import trivia
from api.external import get_weather
from dotenv import load_dotenv
from game_constants import GAME_PROGRESSION, BOSS_BATTLE_COINS, REQUIRED_CLUES, NEXUS_WEAKNESS_KEYWORDS, COIN_CRUNCHER_CONFIG
from functools import wraps
import os
import json
import time
import random
from datetime import datetime

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
    join_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_login = db.Column(db.DateTime, default=db.func.current_timestamp())
    boss_attempts = db.Column(db.Integer, default=0)
    victories = db.Column(db.Integer, default=0)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime, default=db.func.current_timestamp())

# Models for the coin and clue system
class PlayerCoins(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    coins = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=db.func.current_timestamp())

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

class BossProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    weaknesses_found = db.Column(db.Integer, default=0)
    conversation_history = db.Column(db.Text, default='[]')  # JSON string of conversation
    stage = db.Column(db.String(20), default='intro')  # intro, battle, weakness, escape
    started_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class CoinTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Positive for earned, negative for spent/stolen
    source = db.Column(db.String(50), nullable=False)  # game name, cruncher, unlock, etc.
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Custom decorator to check game access
def game_access_required(game_id):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            # Skip access check for clickmaster (first game is always accessible)
            if game_id != 'clickmaster':
                # Get user's coins
                player_coins = PlayerCoins.query.filter_by(user_id=current_user.id).first()
                user_coins = player_coins.coins if player_coins else 0
                
                # Check if user has enough coins to access the game
                required_coins = GAME_PROGRESSION[game_id]['coins_required']
                
                if user_coins < required_coins:
                    flash(f"You need {required_coins} coins to unlock this game. You have {user_coins} coins.")
                    return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    if current_user.is_authenticated:
        # Get user's coins
        player_coins = PlayerCoins.query.filter_by(user_id=current_user.id).first()
        user_coins = player_coins.coins if player_coins else 0
        
        # Determine which games are unlocked
        games_info = {}
        for game_id, game_data in GAME_PROGRESSION.items():
            # Check if the game is unlocked based on coins
            unlocked = user_coins >= game_data['coins_required']
            
            # Get count of discovered clues for this game
            clue_count = DiscoveredClue.query.filter_by(
                user_id=current_user.id,
                game_name=game_id
            ).count()
            
            # Get the user's highest score for this game
            high_score = db.session.query(db.func.max(Score.score)) \
                .filter_by(user_id=current_user.id, game=game_id) \
                .scalar()
            
            games_info[game_id] = {
                'display_name': game_data['display_name'],
                'description': game_data['description'],
                'order': game_data['order'],
                'unlocked': unlocked,
                'coins_required': game_data['coins_required'],
                'coins_needed': max(0, game_data['coins_required'] - user_coins),
                'has_clues': clue_count > 0,
                'high_score': high_score if high_score else 0
            }
        
        # Check if boss battle is available
        clue_count = DiscoveredClue.query.filter_by(user_id=current_user.id).count()
        boss_available = clue_count >= REQUIRED_CLUES and user_coins >= BOSS_BATTLE_COINS
        
        return render_template('index.html', 
                             games=games_info, 
                             user_coins=user_coins,
                             boss_available=boss_available,
                             required_clues=REQUIRED_CLUES,
                             boss_coins=BOSS_BATTLE_COINS)
    else:
        return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            # Update last login timestamp
            user.last_login = datetime.now()
            db.session.commit()
            
            login_user(user)
            return redirect(url_for('index'))
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
    
    # Get recent coin transactions
    transactions = CoinTransaction.query.filter_by(user_id=current_user.id) \
                                .order_by(CoinTransaction.timestamp.desc()) \
                                .limit(10) \
                                .all()
    
    # Get user's boss battle attempts and victories
    boss_attempts = current_user.boss_attempts
    victories = current_user.victories
    
    return render_template('profile.html', 
                          user=current_user, 
                          scores=scores, 
                          games_played=games_played,
                          coins=coins,
                          clues=clues,
                          transactions=transactions,
                          boss_attempts=boss_attempts,
                          victories=victories)

# Game Routes with score submission and clue discovery
@app.route('/games/clickmaster', methods=['GET', 'POST'])
@game_access_required('clickmaster')
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
            
            # Record the coin transaction
            transaction = CoinTransaction(
                user_id=current_user.id,
                amount=3,
                source='clickmaster_clue'
            )
            db.session.add(transaction)
            
            # Check if the clue exists, create it if not
            clue = GameClue.query.filter_by(game_name='clickmaster', clue_id=1).first()
            if not clue:
                clue = GameClue(
                    game_name='clickmaster',
                    clue_id=1,
                    clue_text=GAME_PROGRESSION['clickmaster']['clue_text']
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

@app.route('/games/emoji_memory', methods=['GET', 'POST'])
@game_access_required('emoji_memory')
def emoji_memory():
    if request.method == 'POST':
        data = request.json
        score = data.get('score', 0)
        
        # Save the score
        new_score = Score(user_id=current_user.id, game='emoji_memory', score=score)
        db.session.add(new_score)
        
        # Initialize response data
        response_data = {'message': 'Score saved'}
        
        # Award coins based on score (matching all pairs)
        if score == 8:  # If all 8 pairs are matched
            # Award 5 coins
            player_coins = PlayerCoins.query.filter_by(user_id=current_user.id).first()
            if player_coins:
                player_coins.coins += 5
            else:
                player_coins = PlayerCoins(user_id=current_user.id, coins=5)
                db.session.add(player_coins)
            
            # Record the coin transaction
            transaction = CoinTransaction(
                user_id=current_user.id,
                amount=5,
                source='emoji_memory_complete'
            )
            db.session.add(transaction)
            
            # Add clue if all pairs were matched
            clue = GameClue.query.filter_by(game_name='emoji_memory', clue_id=1).first()
            if not clue:
                clue = GameClue(
                    game_name='emoji_memory',
                    clue_id=1,
                    clue_text=GAME_PROGRESSION['emoji_memory']['clue_text']
                )
                db.session.add(clue)
            
            # Mark clue as discovered if not already
            discovered = DiscoveredClue.query.filter_by(
                user_id=current_user.id,
                game_name='emoji_memory',
                clue_id=1
            ).first()
            
            if not discovered:
                discovered = DiscoveredClue(
                    user_id=current_user.id,
                    game_name='emoji_memory',
                    clue_id=1
                )
                db.session.add(discovered)
            
            # Add clue info to response
            response_data.update({
                'show_clue': True,
                'clue': clue.clue_text,
                'earned_coins': 5
            })
        
        db.session.commit()
        return jsonify(response_data)
    
    return render_template('games/emoji_memory.html')

@app.route('/games/fliptext', methods=['GET', 'POST'])
@game_access_required('fliptext')
def fliptext():
    if request.method == 'POST':
        data = request.json
        input_text = data.get('input', '')
        flipped_text = data.get('output', '')
        
        # Only consider it a valid flip if the text is at least 10 characters
        if len(input_text) >= 10:
            # Award 2 coins for each use (with a daily limit)
            player_coins = PlayerCoins.query.filter_by(user_id=current_user.id).first()
            
            # Check if player has used fliptext today to earn coins
            last_fliptext_transaction = CoinTransaction.query.filter_by(
                user_id=current_user.id,
                source='fliptext_use'
            ).order_by(CoinTransaction.timestamp.desc()).first()
            
            today = datetime.now().date()
            can_earn_coins = True
            
            if last_fliptext_transaction:
                last_usage_date = last_fliptext_transaction.timestamp.date()
                if last_usage_date == today:
                    # Already earned coins today
                    can_earn_coins = False
            
            if can_earn_coins:
                if player_coins:
                    player_coins.coins += 2
                else:
                    player_coins = PlayerCoins(user_id=current_user.id, coins=2)
                    db.session.add(player_coins)
                
                # Record the coin transaction
                transaction = CoinTransaction(
                    user_id=current_user.id,
                    amount=2,
                    source='fliptext_use'
                )
                db.session.add(transaction)
                
                db.session.commit()
                
                response_data = {
                    'message': 'Text flipped and coins awarded',
                    'earned_coins': 2
                }
            else:
                response_data = {
                    'message': 'Text flipped, but you already earned coins today'
                }
            
            # If the input contains "NEXUS" and output has "nexus" (case reversal), award clue
            if "NEXUS" in input_text and "nexus" in flipped_text:
                # Check if clue exists
                clue = GameClue.query.filter_by(game_name='fliptext', clue_id=1).first()
                if not clue:
                    clue = GameClue(
                        game_name='fliptext',
                        clue_id=1,
                        clue_text=GAME_PROGRESSION['fliptext']['clue_text']
                    )
                    db.session.add(clue)
                
                # Mark clue as discovered if not already
                discovered = DiscoveredClue.query.filter_by(
                    user_id=current_user.id,
                    game_name='fliptext',
                    clue_id=1
                ).first()
                
                if not discovered:
                    discovered = DiscoveredClue(
                        user_id=current_user.id,
                        game_name='fliptext',
                        clue_id=1
                    )
                    db.session.add(discovered)
                    
                    # Award additional coins for finding the clue
                    if player_coins:
                        player_coins.coins += 3
                    
                    # Record the coin transaction
                    transaction = CoinTransaction(
                        user_id=current_user.id,
                        amount=3,
                        source='fliptext_clue'
                    )
                    db.session.add(transaction)
                    
                    db.session.commit()
                    
                    # Add clue info to response
                    response_data.update({
                        'show_clue': True,
                        'clue': clue.clue_text,
                        'earned_coins': 3
                    })
            
            return jsonify(response_data)
        else:
            return jsonify({'message': 'Text too short for rewards'})
    
    return render_template('games/fliptext.html')

@app.route('/games/space_dodger', methods=['GET', 'POST'])
@game_access_required('space_dodger')
def space_dodger():
    if request.method == 'POST':
        data = request.json
        score = data.get('score', 0)
        
        # Save the score
        new_score = Score(user_id=current_user.id, game='space_dodger', score=score)
        db.session.add(new_score)
        
        # Initialize response data
        response_data = {'message': 'Score saved'}
        
        # Award coins based on score tiers
        earned_coins = 0
        if score >= 500:
            earned_coins = 10
        elif score >= 300:
            earned_coins = 7
        elif score >= 150:
            earned_coins = 5
        elif score >= 50:
            earned_coins = 2
        
        if earned_coins > 0:
            player_coins = PlayerCoins.query.filter_by(user_id=current_user.id).first()
            if player_coins:
                player_coins.coins += earned_coins
            else:
                player_coins = PlayerCoins(user_id=current_user.id, coins=earned_coins)
                db.session.add(player_coins)
            
            # Record the coin transaction
            transaction = CoinTransaction(
                user_id=current_user.id,
                amount=earned_coins,
                source='space_dodger_score'
            )
            db.session.add(transaction)
            
            response_data['earned_coins'] = earned_coins
        
        # Award clue if score is high enough (500+)
        if score >= 500:
            clue = GameClue.query.filter_by(game_name='space_dodger', clue_id=1).first()
            if not clue:
                clue = GameClue(
                    game_name='space_dodger',
                    clue_id=1,
                    clue_text=GAME_PROGRESSION['space_dodger']['clue_text']
                )
                db.session.add(clue)
            
            # Mark clue as discovered if not already
            discovered = DiscoveredClue.query.filter_by(
                user_id=current_user.id,
                game_name='space_dodger',
                clue_id=1
            ).first()
            
            if not discovered:
                discovered = DiscoveredClue(
                    user_id=current_user.id,
                    game_name='space_dodger',
                    clue_id=1
                )
                db.session.add(discovered)
                
                # Add clue info to response
                response_data.update({
                    'show_clue': True,
                    'clue': clue.clue_text
                })
        
        db.session.commit()
        return jsonify(response_data)
    
    return render_template('games/space_dodger.html')

@app.route('/games/weather_wizard')
@game_access_required('weather_wizard')
def weather_wizard():
    return render_template('games/weather_wizard.html')

@app.route('/games/ai_trivia')
@game_access_required('ai_trivia')
def ai_trivia():
    return render_template('games/ai_trivia.html')

@app.route('/games/boss_battle')
@login_required
def boss_battle():
    # Check if player has enough coins and clues to access the boss battle
    player_coins = PlayerCoins.query.filter_by(user_id=current_user.id).first()
    user_coins = player_coins.coins if player_coins else 0
    
    clue_count = DiscoveredClue.query.filter_by(user_id=current_user.id).count()
    
    if user_coins < BOSS_BATTLE_COINS or clue_count < REQUIRED_CLUES:
        flash(f"You need {BOSS_BATTLE_COINS} coins and {REQUIRED_CLUES} clues to challenge NEXUS. You have {user_coins} coins and {clue_count} clues.")
        return redirect(url_for('index'))
    
    # Get or create boss progress
    boss_progress = BossProgress.query.filter_by(user_id=current_user.id).first()
    if not boss_progress:
        boss_progress = BossProgress(user_id=current_user.id)
        db.session.add(boss_progress)
        
        # Increment boss attempts counter
        current_user.boss_attempts += 1
        db.session.commit()
    
    # Get user's discovered clues to display during battle
    discovered_clues = db.session.query(DiscoveredClue, GameClue) \
                                .join(GameClue, 
                                     (DiscoveredClue.game_name == GameClue.game_name) & 
                                     (DiscoveredClue.clue_id == GameClue.clue_id)) \
                                .filter(DiscoveredClue.user_id == current_user.id) \
                                .all()
    
    clues = [{"game_name": clue.DiscoveredClue.game_name, 
              "clue_text": clue.GameClue.clue_text} 
              for clue in discovered_clues]
    
    return render_template('games/boss_battle.html', 
                          boss_progress=boss_progress, 
                          clues=clues,
                          weaknesses_found=boss_progress.weaknesses_found,
                          stage=boss_progress.stage)