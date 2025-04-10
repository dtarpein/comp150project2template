from main import app, db
from main import init_game_data

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    
    print("Creating new tables...")
    db.create_all()
    
    print("Initializing game data...")
    init_game_data()
    
    print("Database reset complete!")