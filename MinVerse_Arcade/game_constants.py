# Define game unlock requirements and order
GAME_PROGRESSION = {
    'clickmaster': {
        'coins_required': 0,  # First game is free
        'order': 1,
        'display_name': '🔥 ClickMaster',
        'description': 'Test your clicking speed!',
        'clue_text': "The key to defeating NEXUS lies in patterns. Remember: 42 is the answer to everything."
    },
    'fliptext': {
        'coins_required': 10,  # Unlock after earning 10 coins
        'order': 2,
        'display_name': '🔁 FlipText',
        'description': 'Flip the case of your text!',
        'clue_text': "NEXUS fears reversed logic. What looks normal may need to be flipped."
    },
    'emoji_memory': {
        'coins_required': 20,  # Unlock after earning 20 coins
        'order': 3,
        'display_name': '🧠 Emoji Memory',
        'description': 'Match the emoji pairs!',
        'clue_text': "NEXUS has a weak memory for faces. Show it the same pattern twice to confuse it."
    },
    'space_dodger': {
        'coins_required': 35,  # Unlock after earning 35 coins
        'order': 4,
        'display_name': '🌌 Space Dodger',
        'description': 'Dodge the asteroids!',
        'clue_text': "NEXUS cannot predict random movements. Chaos is your ally."
    },
    'weather_wizard': {
        'coins_required': 50,  # Unlock after earning 50 coins
        'order': 5,
        'display_name': '☀️ Weather Wizard',
        'description': 'Check the weather anywhere!',
        'clue_text': "NEXUS overheats easily. Cold climates weaken its defenses."
    },
    'ai_trivia': {
        'coins_required': 75,  # Unlock after earning 75 coins
        'order': 6,
        'display_name': '🧠 AI Trivia',
        'description': 'Test your knowledge!',
        'clue_text': "Knowledge is power. NEXUS has a blind spot about its own creation."
    },
    'boss_battle': {
        'coins_required': 100,  # Final boss requires 100 coins
        'order': 7,
        'display_name': '⚔️ Final Battle',
        'description': 'Confront NEXUS and escape!',
        'clue_text': ""  # No clue for the boss battle itself
    }
}

# Coins required to unlock boss battle
BOSS_BATTLE_COINS = 100

# Number of clues required to attempt the boss battle
REQUIRED_CLUES = 3

# Keywords related to different clue categories for the boss battle
NEXUS_WEAKNESS_KEYWORDS = {
    'pattern': ['pattern', 'patterns', '42', 'forty-two', 'forty two', 'repeat', 'sequence'],
    'reverse': ['reverse', 'reversed', 'flip', 'flipped', 'backward', 'backwards', 'inverse'],
    'memory': ['memory', 'memories', 'remember', 'forget', 'twice', 'repeat', 'same', 'face', 'faces', 'emoji'],
    'random': ['random', 'chaos', 'unpredictable', 'dodge', 'movement', 'moving', 'erratic'],
    'temperature': ['cold', 'freeze', 'freezing', 'temperature', 'climate', 'weather', 'overheat', 'cooling'],
    'knowledge': ['knowledge', 'creation', 'origin', 'creator', 'made', 'built', 'designed', 'blind spot']
}

# Coin cruncher configuration
COIN_CRUNCHER_CONFIG = {
    'min_appearance_interval': 120,  # Minimum seconds between appearances (2 minutes)
    'max_appearance_interval': 300,  # Maximum seconds between appearances (5 minutes)
    'stay_duration': 10,             # How long the cruncher stays if not clicked (seconds)
    'min_steal_amount': 5,           # Minimum coins to steal
    'max_steal_amount': 15,          # Maximum coins to steal
    'click_threshold': 10            # Clicks needed to defeat the coin cruncher
}