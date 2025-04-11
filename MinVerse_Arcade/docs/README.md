# MiniVerse Arcade

MiniVerse Arcade is an immersive web application featuring multiple interactive mini-games with a cohesive narrative. Players are trapped in a digital realm by NEXUS, a rogue AI, and must master games, earn coins, and discover clues to challenge NEXUS and escape the MiniVerse.

## Story & Gameplay

You've been pulled into the MiniVerse by NEXUS, an artificial intelligence that collects humans to study through gameplay. Your goal is to:

1. Master the mini-games to earn coins
2. Unlock new games as you progress
3. Discover hidden clues in each game
4. Use these clues to defeat NEXUS in the final boss battle
5. Escape the MiniVerse!

But beware - the mischievous Coin Cruncher may appear at any time to steal your hard-earned coins!

## Features

### User Experience
- User Authentication (login/register/logout)
- User Profile with Score Tracking
- Progressive Game Unlocking System
- Coins Economy with Transaction History
- Hidden Clues System
- Final Boss Battle with NEXUS
- Victory Sequence

### Mini-Games
- 🔥 ClickMaster: Test your clicking speed
- 🔁 FlipText: Text case transformation tool
- 🧠 Emoji Memory Game: Match pairs of emoji cards
- 🌌 Space Dodger: Avoid obstacles in space
- ☀️ Weather Wizard: Get real-time weather data
- 🧠 AI Trivia: AI-generated questions
- ⚔️ Final Battle: Challenge NEXUS using discovered clues

### Technical Components
- Flask web framework with SQLAlchemy ORM
- User authentication with Flask-Login
- SQLite database for data persistence
- Interactive JavaScript for game logic
- Dynamic portal animations and visual effects
- External API integration (OpenWeatherMap)
- AI integration with OpenAI's GPT models
- Dynamic sound effects and visual feedback
- Responsive CSS design

## Setup Instructions
1. Clone the repository
2. Create a .env file with the following variables:
```
SECRET_KEY=your_random_secret_key_here
OPENAI_API_KEY=your_openai_api_key
WEATHER_API_KEY=your_openweathermap_api_key
```
3. Install dependencies using Poetry:
```bash
poetry install
```

4. Initialize the database:
```bash
poetry run python
>>> from main import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

5. Run the application:
```bash
poetry run python main.py
```

6. Open a browser and navigate to http://localhost:5000

## Gameplay Hints

- **ClickMaster**: Look for a special number that might reveal a clue
- **FlipText**: Try flipping text containing "NEXUS"
- **Emoji Memory**: Complete a full game to discover its secret
- **Space Dodger**: Reach a high score to unlock a clue
- **Weather Wizard**: Check cold cities to discover NEXUS's weakness
- **AI Trivia**: Look for questions about artificial intelligence

## Final Battle Strategy

The final confrontation with NEXUS requires strategic thinking. Use the clues you've collected to formulate messages that exploit NEXUS's weaknesses. Try combining concepts from multiple clues in a single message to create system glitches.

## Deployment

The application is configured for deployment on platforms supporting Python web applications:
- Includes Gunicorn for production serving
- .replit configuration for Replit deployment
- Can be easily deployed to Heroku, Render, or similar platforms

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.