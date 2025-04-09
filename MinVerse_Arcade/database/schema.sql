-- Add these new tables to your schema.sql file

-- Table to track player coins
CREATE TABLE IF NOT EXISTS player_coins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    coins INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Table to track which clues a player has discovered
CREATE TABLE IF NOT EXISTS discovered_clues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    game_name TEXT NOT NULL,
    clue_id INTEGER NOT NULL,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, game_name, clue_id)
);

-- Table to store game clues
CREATE TABLE IF NOT EXISTS game_clues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_name TEXT NOT NULL,
    clue_id INTEGER NOT NULL,
    clue_text TEXT NOT NULL,
    UNIQUE(game_name, clue_id)
);

-- Insert initial clues for each game
INSERT OR IGNORE INTO game_clues (game_name, clue_id, clue_text) VALUES 
('clickmaster', 1, 'The key to defeating NEXUS lies in patterns. Remember: 42 is the answer to everything.'),
('fliptext', 1, 'NEXUS fears reversed logic. What looks normal may need to be flipped.'),
('emoji_memory', 1, 'NEXUS has a weak memory for faces. Show it the same pattern twice to confuse it.'),
('space_dodger', 1, 'NEXUS cannot predict random movements. Chaos is your ally.'),
('weather_wizard', 1, 'NEXUS overheats easily. Cold climates weaken its defenses.'),
('ai_trivia', 1, 'Knowledge is power. NEXUS has a blind spot about its own creation.');