document.getElementById('flip-button').onclick = () => {
  const input = document.getElementById('flip-input').value;
  const flipped = input
    .split('')
    .map(c => c === c.toLowerCase() ? c.toUpperCase() : c.toLowerCase())
    .join('');
  document.getElementById('flip-output').innerText = flipped;
  
  // Check if the input is long enough to earn coins
  if (input.length >= 10) {
    // Send the flipped text to the server
    fetch('/games/fliptext', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        input: input,
        output: flipped
      })
    })
    .then(res => res.json())
    .then(data => {
      console.log("Server response:", data);  // Debug line to see server response
      console.log("Input:", input);           // Debug line to check input
      console.log("Output:", flipped);        // Debug line to check output
      
      // If coins were earned, show a notification
      if (data.earned_coins) {
        showNotification(`You earned ${data.earned_coins} coins!`);
        playSound('coin-earned');
      }
      
      // If a clue was discovered, show the clue modal
      if (data.show_clue) {
        showClueModal(data.clue, data.earned_coins);
      }
    })
    .catch(err => console.error('Error:', err));
  } else if (input.length > 0) {
    // Text too short but not empty
    showNotification("Text must be at least 10 characters long to earn coins.");
  }
};

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

// Play sound
function playSound(soundName) {
  try {
    const audio = new Audio(`/static/media/sounds/${soundName}.mp3`);
    audio.play().catch(err => console.log('Audio playback error:', err));
  } catch (e) {
    console.error('Error playing sound:', e);
  }
}

// Add instructions when the page loads
document.addEventListener('DOMContentLoaded', () => {
  // Add instructions to the page
  const instructionsDiv = document.createElement('div');
  instructionsDiv.className = 'game-instructions';
  instructionsDiv.innerHTML = `
    <h3>Instructions:</h3>
    <ul>
      <li>Enter text (at least 10 characters long) in the box and click "Flip Case" to transform it</li>
      <li>You earn 2 coins once per day for using this tool</li>
      <li><em>Hint: Try flipping text containing "NEXUS" to discover a hidden clue!</em></li>
    </ul>
  `;
  
  // Insert after the flip button
  const flipButton = document.getElementById('flip-button');
  flipButton.parentNode.insertBefore(instructionsDiv, flipButton.nextSibling);
  
  // Add styles
  const style = document.createElement('style');
  style.textContent = `
    .game-instructions {
      background-color: rgba(153, 50, 204, 0.1);
      border-left: 3px solid #9932CC;
      padding: 10px 15px;
      margin: 15px 0;
      border-radius: 5px;
    }
    .game-instructions h3 {
      color: #9932CC;
      margin-top: 0;
    }
    .game-instructions ul {
      text-align: left;
    }
  `;
  document.head.appendChild(style);
});