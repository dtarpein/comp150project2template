const emojis = ['🐶', '🐱', '🐭', '🐹', '🦊', '🐻', '🐼', '🐨'];
let gameGrid = [...emojis, ...emojis].sort(() => 0.5 - Math.random());

const grid = document.getElementById('memory-game');
let first = null, second = null, matches = 0;
let canFlip = true;

gameGrid.forEach(emoji => {
  const card = document.createElement('div');
  card.className = 'card';
  card.textContent = '?';
  card.dataset.emoji = emoji;
  card.onclick = () => {
    if (!canFlip || card.classList.contains('matched') || card === first) return;
    
    card.textContent = emoji;

    if (!first) {
      first = card;
    } else {
      canFlip = false;
      second = card;
      
      if (first.dataset.emoji === second.dataset.emoji) {
        // Match found
        first.classList.add('matched');
        second.classList.add('matched');
        matches++;
        document.getElementById('match-count').innerText = matches;
        
        // Play match sound with error handling
        new Audio('/static/media/sounds/match.mp3')
          .play()
          .catch(err => console.log('Audio playback error:', err));
        
        // Submit score when all matches are found
        if (matches === emojis.length) {
          fetch('/games/emoji_memory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ score: matches })
          })
          .then(res => res.json())
          .then(data => {
            alert('Game complete! Score saved.');
            console.log(data.message);
          })
          .catch(err => console.error('Error saving score:', err));
        }
        
        first = second = null;
        canFlip = true;
      } else {
        // No match
        // FIXED: Using consistent path format for the fail sound
        new Audio('/static/media/sounds/fail.mp3')
          .play()
          .catch(err => console.log('Audio playback error:', err));
        
        setTimeout(() => {
          first.textContent = '?';
          second.textContent = '?';
          first = second = null;
          canFlip = true;
        }, 800);
      }
    }
  };
  grid.appendChild(card);
});
