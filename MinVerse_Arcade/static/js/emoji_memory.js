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
        playSound('match');
        
        // Submit score when all matches are found
        if (matches === emojis.length) {
          // Wait a moment before showing victory
          setTimeout(() => {
            fetch('/games/emoji_memory', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ score: matches })
            })
            .then(res => res.json())
            .then(data => {
              console.log(data.message);
              
              // Check if coins were earned
              if (data.earned_coins) {
                showNotification(`You earned ${data.earned_coins} coins!`);
              }
              
              // Check if a clue was discovered
              if (data.show_clue) {
                showClueModal(data.clue, data.earned_coins);
              } else {
                // If no clue, just show game complete
                alert('Game complete! All pairs matched!');
              }
            })
            .catch(err => console.error('Error saving score:', err));
          }, 500);
        }
        
        first = second = null;
        canFlip = true;
      } else {
        // No match
        playSound('fail');
        
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

// Play sound
function playSound(soundName) {
  try {
    const audio = new Audio(`/static/media/sounds/${soundName}.mp3`);
    audio.play().catch(err => console.log('Audio playback error:', err));
  } catch (e) {
    console.error('Error playing sound:', e);
  }
}

// Create a notification element
function showNotification(message) {
  // Check if notification already exists
  let notification = document.getElementById('coin-notification');
  
  if (!notification) {
    // Create new notification
    notification = document.createElement('div');
    notification.id = 'coin-notification';
    notification.style.position = 'fixed';
    notification.style.bottom = '20px';
    notification.style.right = '20px';
    notification.style.backgroundColor = '#FFD700';
    notification.style.color = '#333';
    notification.style.padding = '10px 20px';
    notification.style.borderRadius = '5px';
    notification.style.zIndex = '1000';
    notification.style.opacity = '0';
    notification.style.transition = 'opacity 0.3s';
    
    document.body.appendChild(notification);
  }
  
  // Update message and show
  notification.textContent = message;
  setTimeout(() => {
    notification.style.opacity = '1';
  }, 10);
  
  // Hide after 3 seconds
  setTimeout(() => {
    notification.style.opacity = '0';
  }, 3000);
}

// Create and show clue modal
function showClueModal(clueText, earnedCoins) {
  // Create modal if it doesn't exist
  let modal = document.getElementById('clue-modal');
  
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'clue-modal';
    modal.style.position = 'fixed';
    modal.style.top = '0';
    modal.style.left = '0';
    modal.style.width = '100%';
    modal.style.height = '100%';
    modal.style.backgroundColor = 'rgba(0,0,0,0.7)';
    modal.style.display = 'flex';
    modal.style.justifyContent = 'center';
    modal.style.alignItems = 'center';
    modal.style.zIndex = '2000';
    
    const content = document.createElement('div');
    content.style.backgroundColor = '#2d3436';
    content.style.padding = '30px';
    content.style.borderRadius = '10px';
    content.style.maxWidth = '500px';
    content.style.width = '80%';
    content.style.textAlign = 'center';
    content.style.position = 'relative';
    content.style.border = '2px solid #9932CC';
    content.style.boxShadow = '0 0 20px #9932CC';
    
    const title = document.createElement('h3');
    title.textContent = '🔍 You\'ve Discovered a Clue!';
    title.style.color = '#9932CC';
    
    const clueTextElement = document.createElement('p');
    clueTextElement.id = 'clue-text';
    clueTextElement.style.margin = '20px 0';
    clueTextElement.style.lineHeight = '1.5';
    
    const coinsInfo = document.createElement('div');
    coinsInfo.style.backgroundColor = '#FFD700';
    coinsInfo.style.color = '#333';
    coinsInfo.style.padding = '10px';
    coinsInfo.style.borderRadius = '5px';
    coinsInfo.style.margin = '20px 0';
    coinsInfo.innerHTML = `<span style="margin-right: 5px;">💰</span> You earned <span id="earned-coins-text"></span> coins!`;
    
    const closeButton = document.createElement('button');
    closeButton.textContent = 'Remember this clue';
    closeButton.style.backgroundColor = '#9932CC';
    closeButton.style.color = 'white';
    closeButton.style.border = 'none';
    closeButton.style.padding = '10px 20px';
    closeButton.style.borderRadius = '5px';
    closeButton.style.cursor = 'pointer';
    closeButton.onclick = () => {
      modal.style.display = 'none';
    };
    
    content.appendChild(title);
    content.appendChild(clueTextElement);
    content.appendChild(coinsInfo);
    content.appendChild(closeButton);
    modal.appendChild(content);
    
    document.body.appendChild(modal);
  }
  
  // Update content and show modal
  document.getElementById('clue-text').textContent = clueText;
  document.getElementById('earned-coins-text').textContent = earnedCoins;
  modal.style.display = 'flex';
  
  // Play clue sound
  playSound('clue-discovered');
}