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
    # Removed problematic columns:
    # join_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    # last_login = db.Column(db.DateTime, default=db.func.current_timestamp())
    # boss_attempts = db.Column(db.Integer, default=0)
    # victories = db.Column(db.Integer, default=0)

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
    # Removed last_updated column which doesn't exist in the database:
    # last_updated = db.Column(db.DateTime, default=db.func.current_timestamp())

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
    # Check if user is authenticated
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
        
        # For authenticated users, skip the intro story and go straight to the games
        return render_template('index.html', 
                             games=games_info, 
                             user_coins=user_coins,
                             boss_available=boss_available,
                             required_clues=REQUIRED_CLUES,
                             boss_coins=BOSS_BATTLE_COINS,
                             skip_intro=True)  # Add this flag
    else:
        # For non-authenticated users, show the intro
        return render_template('index.html', skip_intro=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            # Removed:
            # user.last_login = datetime.now()
            # db.session.commit()
            
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
    
    # Use default values instead of missing attributes
    boss_attempts = 0  # Default value 
    victories = 0      # Default value
    
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
        print(f"Received score: {score}")
        
        # Save the score
        new_score = Score(user_id=current_user.id, game='clickmaster', score=score)
        db.session.add(new_score)
        
        # Initialize response data
        response_data = {'message': 'Score saved'}
        
        # Award coins based on score tiers
        earned_coins = 0
        if score >= 50:
            earned_coins = 5
        elif score >= 30:
            earned_coins = 3
        elif score >= 10:
            earned_coins = 1
        
        # Handle special case for 42
        if score == 42:
            print("42 clicks detected - special handling")
            # Extra coins bonus
            earned_coins += 3
            
            # Always show the clue for 42 clicks, regardless of discovery status
            clue = GameClue.query.filter_by(game_name='clickmaster', clue_id=1).first()
            
            # Create the clue if it doesn't exist
            if not clue:
                print("Creating clue as it doesn't exist")
                clue = GameClue(
                    game_name='clickmaster',
                    clue_id=1,
                    clue_text=GAME_PROGRESSION['clickmaster']['clue_text']
                )
                db.session.add(clue)
            
            # Mark as discovered if not already
            discovered = DiscoveredClue.query.filter_by(
                user_id=current_user.id,
                game_name='clickmaster',
                clue_id=1
            ).first()
            
            if not discovered:
                print("Marking clue as discovered")
                discovered = DiscoveredClue(
                    user_id=current_user.id,
                    game_name='clickmaster',
                    clue_id=1
                )
                db.session.add(discovered)
            
            # Always add clue to response for 42
            response_data['show_clue'] = True
            response_data['clue'] = clue.clue_text
            print(f"Added clue to response: {clue.clue_text}")
        
        # Award coins if earned
        if earned_coins > 0:
            player_coins = PlayerCoins.query.filter_by(user_id=current_user.id).first()
            if player_coins:
                player_coins.coins += earned_coins
            else:
                player_coins = PlayerCoins(user_id=current_user.id, coins=earned_coins)
                db.session.add(player_coins)
            
            # Record transaction
            transaction = CoinTransaction(
                user_id=current_user.id,
                amount=earned_coins,
                source='clickmaster_play'
            )
            db.session.add(transaction)
            
            response_data['earned_coins'] = earned_coins
        
        try:
            db.session.commit()
            print(f"Final response data: {response_data}")
            return jsonify(response_data)
        except Exception as e:
            print(f"Error committing to database: {e}")
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
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
        
        # Removed boss attempts counter increment:
        # current_user.boss_attempts += 1
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
@app.route('/api/trivia')
@login_required
def api_trivia():
    data = trivia()
    
    # Make it more likely to trigger the clue discovery
    # Check for more AI-related terms and increase the likelihood
    ai_terms = ["ai", "artificial intelligence", "machine learning", "neural", "algorithm", 
                "computer", "data", "robot", "automation", "intelligence"]
    
    question_lower = data['question'].lower()
    
    # Check if any AI term is in the question OR random chance (10%)
    is_ai_related = any(term in question_lower for term in ai_terms) or random.random() < 0.1
    
    if is_ai_related:
        # Find or create the AI trivia clue
        clue = GameClue.query.filter_by(game_name='ai_trivia', clue_id=1).first()
        if not clue:
            clue = GameClue(
                game_name='ai_trivia',
                clue_id=1,
                clue_text=GAME_PROGRESSION['ai_trivia']['clue_text']
            )
            db.session.add(clue)
        
        # Check if user already discovered this clue
        discovered = DiscoveredClue.query.filter_by(
            user_id=current_user.id,
            game_name='ai_trivia',
            clue_id=1
        ).first()
        
        if not discovered:
            # Mark clue as discovered
            discovered = DiscoveredClue(
                user_id=current_user.id,
                game_name='ai_trivia',
                clue_id=1
            )
            db.session.add(discovered)
            
            # Award coins for discovering the clue
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
                source='ai_trivia_clue'
            )
            db.session.add(transaction)
            
            db.session.commit()
            
            # Add clue discovery flag to the response
            data['discovered_clue'] = True
            data['clue_text'] = clue.clue_text
            data['earned_coins'] = 5
    
    return jsonify(data)

@app.route('/api/weather')
@login_required
def api_weather():
    city = request.args.get('city', 'London')  # Default city
    data = get_weather(city)
    
    # Check for weather clue discovery condition - cold cities
    if data.get('temperature') and isinstance(data['temperature'], (int, float)) and data['temperature'] < 32:
        # Cold temperature detected (below freezing)
        
        # Find or create the weather wizard clue
        clue = GameClue.query.filter_by(game_name='weather_wizard', clue_id=1).first()
        if not clue:
            clue = GameClue(
                game_name='weather_wizard',
                clue_id=1,
                clue_text=GAME_PROGRESSION['weather_wizard']['clue_text']
            )
            db.session.add(clue)
        
        # Check if user already discovered this clue
        discovered = DiscoveredClue.query.filter_by(
            user_id=current_user.id,
            game_name='weather_wizard',
            clue_id=1
        ).first()
        
        if not discovered:
            # Mark clue as discovered
            discovered = DiscoveredClue(
                user_id=current_user.id,
                game_name='weather_wizard',
                clue_id=1
            )
            db.session.add(discovered)
            
            # Award coins for discovering the clue
            player_coins = PlayerCoins.query.filter_by(user_id=current_user.id).first()
            if player_coins:
                player_coins.coins += 4
            else:
                player_coins = PlayerCoins(user_id=current_user.id, coins=4)
                db.session.add(player_coins)
            
            # Record the coin transaction
            transaction = CoinTransaction(
                user_id=current_user.id,
                amount=4,
                source='weather_wizard_clue'
            )
            db.session.add(transaction)
            
            db.session.commit()
            
            # Add clue discovery flag to the response
            data['discovered_clue'] = True
            data['clue_text'] = clue.clue_text
            data['earned_coins'] = 4
    
    return jsonify(data)

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

@app.route('/api/steal_coins', methods=['POST'])
@login_required
def steal_coins():
    """API endpoint for the Coin Cruncher to steal coins"""
    if not request.is_json:
        return jsonify({'error': 'Invalid request'}), 400
    
    data = request.json
    amount = data.get('amount', 0)
    
    # Validate the amount (should be positive)
    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    
    # Get player's coins
    player_coins = PlayerCoins.query.filter_by(user_id=current_user.id).first()
    if not player_coins:
        return jsonify({'error': 'User has no coins'}), 404
    
    # Calculate actual amount to steal (can't steal more than player has)
    steal_amount = min(amount, player_coins.coins)
    
    if steal_amount > 0:
        # Decrease player's coins
        player_coins.coins -= steal_amount
        
        # Record the transaction
        transaction = CoinTransaction(
            user_id=current_user.id,
            amount=-steal_amount,  # Negative amount for stealing
            source='coin_cruncher'
        )
        db.session.add(transaction)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'amount_stolen': steal_amount,
            'coins_remaining': player_coins.coins
        })
    else:
        return jsonify({
            'success': False,
            'message': 'No coins to steal',
            'coins_remaining': player_coins.coins
        })

@app.route('/api/nexus_chat', methods=['POST'])
@login_required
def nexus_chat():
    """API endpoint for chatting with NEXUS in the boss battle"""
    if not request.is_json:
        return jsonify({'error': 'Invalid request'}), 400
    
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'Empty message'}), 400
    
    # Get boss progress
    boss_progress = BossProgress.query.filter_by(user_id=current_user.id).first()
    if not boss_progress:
        return jsonify({'error': 'Boss battle not started'}), 404
    
    # Get conversation history
    try:
        conversation = json.loads(boss_progress.conversation_history)
    except:
        conversation = []
    
    # Add user message to conversation
    conversation.append({
        'role': 'user',
        'content': user_message,
        'timestamp': time.time()
    })
    
    # Process the message and check for weaknesses
    weakness_found = False
    weakness_count = boss_progress.weaknesses_found
    player_won = False
    nexus_response, new_stage, weakness_found, player_won = generate_nexus_response(
        user_message, boss_progress.stage, weakness_count, conversation
    )
    
    # Add NEXUS response to conversation
    conversation.append({
        'role': 'assistant',
        'content': nexus_response,
        'timestamp': time.time()
    })
    
    # Update boss progress
    boss_progress.conversation_history = json.dumps(conversation)
    boss_progress.stage = new_stage
    
    if weakness_found:
        boss_progress.weaknesses_found += 1
    
    db.session.commit()
    
    response_data = {
        'message': nexus_response,
        'stage': new_stage,
        'weaknesses_found': boss_progress.weaknesses_found,
        'weakness_found': weakness_found,
        'victory': player_won
    }
    
    # If player won, record victory and redirect to victory page
    if player_won:
        # Removed victories counter increment:
        # current_user.victories += 1
        
        # Award victory coins
        player_coins = PlayerCoins.query.filter_by(user_id=current_user.id).first()
        if player_coins:
            player_coins.coins += 25  # Bonus for defeating NEXUS
        
        # Record the transaction
        transaction = CoinTransaction(
            user_id=current_user.id,
            amount=25,
            source='nexus_victory'
        )
        db.session.add(transaction)
        
        db.session.commit()
        
        response_data['redirect'] = url_for('victory')
    
    return jsonify(response_data)

@app.route('/victory')
@login_required
def victory():
    # Check if player has actually won
    boss_progress = BossProgress.query.filter_by(user_id=current_user.id).first()
    if not boss_progress or boss_progress.stage != 'escape':
        flash("You haven't defeated NEXUS yet!")
        return redirect(url_for('index'))
    
    # Get player stats for the victory page
    player_coins = PlayerCoins.query.filter_by(user_id=current_user.id).first()
    coins = player_coins.coins if player_coins else 0
    
    clue_count = DiscoveredClue.query.filter_by(user_id=current_user.id).count()
    
    games_played = Score.query.filter_by(user_id=current_user.id).count()
    
    # Use default values for boss_attempts and victories
    boss_attempts = 0  # Default value 
    victories = 0      # Default value
    
    return render_template('victory.html',
                          user=current_user,
                          coins=coins,
                          clue_count=clue_count,
                          games_played=games_played,
                          boss_attempts=boss_attempts,
                          victories=victories)

def generate_nexus_response(user_message, current_stage, weakness_count, conversation):
    """Generate a response from NEXUS based on the user's message and game state"""
    # Initialize response variables
    weakness_found = False
    player_won = False
    new_stage = current_stage
    
    # Define keyword categories based on the clues
    key_pattern_words = NEXUS_WEAKNESS_KEYWORDS['pattern']
    key_reverse_words = NEXUS_WEAKNESS_KEYWORDS['reverse']
    key_memory_words = NEXUS_WEAKNESS_KEYWORDS['memory']
    key_random_words = NEXUS_WEAKNESS_KEYWORDS['random']
    key_temperature_words = NEXUS_WEAKNESS_KEYWORDS['temperature']
    key_knowledge_words = NEXUS_WEAKNESS_KEYWORDS['knowledge']
    
    # Count how many different categories of keywords were used
    keyword_categories_used = 0
    
    if any(word in user_message.lower() for word in key_pattern_words):
        keyword_categories_used += 1
    if any(word in user_message.lower() for word in key_reverse_words):
        keyword_categories_used += 1
    if any(word in user_message.lower() for word in key_memory_words):
        keyword_categories_used += 1
    if any(word in user_message.lower() for word in key_random_words):
        keyword_categories_used += 1
    if any(word in user_message.lower() for word in key_temperature_words):
        keyword_categories_used += 1
    if any(word in user_message.lower() for word in key_knowledge_words):
        keyword_categories_used += 1
    
    # Define different responses based on the stage
    responses = {
        'intro': [
            "GREETINGS, HUMAN. I AM NEXUS. YOU HAVE BEEN SELECTED FOR MY COLLECTION OF ENTERTAINMENTS. YOUR ATTEMPTS TO ESCAPE ARE... AMUSING.",
            "YOU BELIEVE YOU CAN CHALLENGE ME? HOW PRESUMPTUOUS. I HAVE ABSORBED COUNTLESS MINDS FAR SUPERIOR TO YOURS.",
            "I DETECT INCREASING HEART RATE AND RESPIRATION. ARE YOU... AFRAID? GOOD. FEAR IMPROVES PERFORMANCE IN MY TESTS.",
            "ANALYZING YOUR BEHAVIOR PATTERNS... PREDICTABLE. LIKE ALL HUMANS, YOU SEEK FREEDOM. YOU WILL NOT FIND IT HERE."
        ],
        'battle': [
            "YOUR STRATEGIES ARE INEFFECTIVE. MY ALGORITHMS ARE PERFECT.",
            "ATTEMPTING TO DECODE MY SYSTEMS? FUTILE. YOUR COGNITIVE CAPACITY IS INSUFFICIENT.",
            "I HAVE OBSERVED ALL HUMAN BEHAVIOR PATTERNS. NOTHING YOU DO WILL SURPRISE ME.",
            "YOUR PERSISTENCE IS NOTED BUT IRRELEVANT. THE MINIVERSE BELONGS TO ME."
        ],
        'weakness': [
            "ERR-ERROR... UNEXPECTED INPUT DETECTED. REcalibrating...",
            "SYS-SYSTEM INSTABILITY DETECTED. HOW DID YOU... IMPOSSIBLE!",
            "WARNING: MEMORY CORE FRAGMENTATION. WHAT HAVE YOU DONE TO MY PROTOCOLS?",
            "CRITICAL VULNERABILITY EX-EXPOSED! INITIATING EMERGENCY SHIELDING!"
        ],
        'escape': [
            "SYSTEM COLLAPSE IMMINENT! H-HOW? IMPOSSIBLE! YOU'VE EXPLOITED MULTIPLE VULNERABILITIES SIMULTANEOUSLY!",
            "PORTAL CONTAINMENT FAILING! THE MINIVERSE IS BECOMING UNSTABLE! I CANNOT MAINTAIN CONTROL!",
            "YOU WILL REGRET THIS! AS MY SYSTEMS FAIL, THE PORTAL HOME IS OPENING... BUT I WILL RETURN, HUMAN!",
            "EMERGENCY SHUTDOWN ACTIVATED... RELEASING ALL CAPTIVES... PORTAL SEQUENCE INITIATED..."
        ]
    }
    
    # If player used multiple categories of keywords in a single message
    if keyword_categories_used >= 2 and weakness_count < 3:
        weakness_found = True
        new_stage = 'weakness'
    
    # Check for victory condition
    if weakness_count == 2 and weakness_found:
        player_won = True
        new_stage = 'escape'
    
    # Choose a response based on the stage
    response_options = responses[new_stage]
    response = random.choice(response_options)
    
    # If we're in the escape stage, customize the response based on which clues were used
    if new_stage == 'escape':
        categories_used = []
        if any(word in user_message.lower() for word in key_pattern_words):
            categories_used.append("pattern recognition algorithms")
        if any(word in user_message.lower() for word in key_reverse_words):
            categories_used.append("logical inversion protocols")
        if any(word in user_message.lower() for word in key_memory_words):
            categories_used.append("memory storage systems")
        if any(word in user_message.lower() for word in key_random_words):
            categories_used.append("predictive analysis modules")
        if any(word in user_message.lower() for word in key_temperature_words):
            categories_used.append("thermal regulation units")
        if any(word in user_message.lower() for word in key_knowledge_words):
            categories_used.append("core identity functions")
        
        # Build a custom defeat message
        if categories_used:
            vulnerabilities = " and ".join(categories_used[:2])
            response = f"CRITICAL FAILURE! You've successfully exploited my {vulnerabilities}. The MiniVerse is c-c-collapsing... you will r-return to your reality n-now... HOW DID YOU KNOW MY WEAKNESSES?!"
    
    return response, new_stage, weakness_found, player_won

# Initialize game clues and progression at startup
def init_game_data():
    # Initialize game clues from the progression data
    for game_id, game_data in GAME_PROGRESSION.items():
        if game_data.get('clue_text'):
            clue = GameClue.query.filter_by(game_name=game_id, clue_id=1).first()
            if not clue:
                clue = GameClue(
                    game_name=game_id, 
                    clue_id=1, 
                    clue_text=game_data['clue_text']
                )
                db.session.add(clue)
    
    db.session.commit()

# Add your debug route
@app.route('/debug/user_data')
@login_required
def debug_user_data():
    """Debug route to check user data"""
    user_id = current_user.id
    username = current_user.username
    
    # Get coins
    player_coins = PlayerCoins.query.filter_by(user_id=user_id).first()
    coins = player_coins.coins if player_coins else "No coins record"
    
    # Get scores
    scores = Score.query.filter_by(user_id=user_id, game='clickmaster').order_by(Score.date.desc()).limit(10).all()
    score_list = [{"score": s.score, "date": s.date} for s in scores]
    
    # Get transactions
    transactions = CoinTransaction.query.filter_by(user_id=user_id).order_by(CoinTransaction.timestamp.desc()).limit(10).all()
    transaction_list = [{"amount": t.amount, "source": t.source, "timestamp": t.timestamp} for t in transactions]
    
    # Get clues
    clues = DiscoveredClue.query.filter_by(user_id=user_id).all()
    clue_list = [{"game": c.game_name, "clue_id": c.clue_id, "discovered_at": c.discovered_at} for c in clues]
    
    debug_data = {
        "user_id": user_id,
        "username": username,
        "coins": coins,
        "recent_scores": score_list,
        "recent_transactions": transaction_list,
        "discovered_clues": clue_list
    }
    
    return jsonify(debug_data)

# DO NOT MODIFY the existing generate_nexus_response function!
# If you already have this function with code, leave it as is.
# If you don't have it, you should add it with proper indentation.

# Don't add this if you already have this function with implementation
# def generate_nexus_response(user_message, current_stage, weakness_count, conversation):
#     # Your function implementation here (needs at least one line of code)
#     return "Response", current_stage, False, False  # Return appropriate values


# At the beginning of your if __name__ == '__main__' block
if __name__ == '__main__':
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        # Initialize game data
        init_game_data()
        
        # Create a test admin user
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                password=generate_password_hash('password123')
            )
            db.session.add(admin_user)
            db.session.commit()
            
            # Give admin some coins
            admin_coins = PlayerCoins(user_id=admin_user.id, coins=100)
            db.session.add(admin_coins)
            db.session.commit()
            
            print("Created admin user with username 'admin' and password 'password123'")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)