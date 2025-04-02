# MiniVerse Arcade

MiniVerse Arcade is a Flask-powered web application featuring multiple interactive mini-games. It leverages HTML, CSS, JavaScript, dynamic audio, HTML5 Canvas animations, GPT-3.5 AI integration, and external APIs for interactive gameplay and dynamic content.

## Features
- User Authentication (login/register/logout)
- User Profile with Score Tracking
- Multiple Mini-Games:
  - 🔥 ClickMaster: Test your clicking speed
  - 🔁 FlipText: Text case transformation tool
  - 🧠 Emoji Memory Game: Match pairs of emoji cards
  - 🌌 Space Dodger: Avoid obstacles in space
  - ☀️ Weather Wizard: Get real-time weather data
  - 🧠 AI Trivia: AI-generated questions powered by GPT-3.5

## Technical Components
- Flask web framework with SQLAlchemy ORM
- User authentication with Flask-Login
- SQLite database for data persistence
- Interactive JavaScript for game logic
- External API integration (OpenWeatherMap)
- AI integration with OpenAI's GPT models
- Dynamic sound effects and visual feedback
- Responsive CSS design

## Setup Instructions
1. Clone the repository
2. Create a .env file with the following variables:
3. Install dependencies using Poetry:
```bash
poetry install

4. Initialize the database:

poetry run python
>>> from main import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()

5. Run the applications
poetry run python main.py

6. Open a browser and navigate to http://localhost:5000
Deployment
The application is configured for deployment on platforms supporting Python web applications:
Includes Gunicorn for production serving
.replit configuration for Replit deployment
Can be easily deployed to Heroku, Render, or similar platforms
Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
