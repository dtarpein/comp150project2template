let clicks = 0;
const clickBtn = document.getElementById('click-btn');
const clickCount = document.getElementById('click-count');
const coinCount = document.getElementById('coin-count');
const clueModal = document.getElementById('clue-modal');
const clueText = document.getElementById('clue-text');
const clueCloseBtn = document.getElementById('clue-close-btn');
const earnedCoinsSpan = document.getElementById('earned-coins');

// Load the user's current coins when the page loads
window.addEventListener('DOMContentLoaded', () => {
  fetchUserCoins();
});

// Fetch the user's current coins from the server
function fetchUserCoins() {
  fetch('/user/coins')
    .then(res => res.json())
    .then(data => {
      coinCount.innerText = data.coins;
    })
    .catch(err => console.error('Error fetching coins:', err));
}

// Handle clicks on the button
clickBtn.onclick = () => {
  clicks++;
  clickCount.innerText = clicks;
  
  // Play sound with error handling
  const audio = new Audio('/static/media/sounds/click.mp3');
  audio.play().catch(err => console.log('Audio playback error:', err));

  // Send score to backend
  if (clicks % 10 === 0 || clicks === 42) {
    sendScore(clicks);
  }
};

// Send the current score to the server
function sendScore(score) {
  fetch('/games/clickmaster', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ score: score })
  })
  .then(res => res.json())
  .then(data => {
    console.log(data.message);
    
    // If the user has earned coins, update the display
    if (data.earned_coins > 0) {
      // Refresh coin count from server to ensure accuracy
      fetchUserCoins();
      
      // Show earned coins in the modal
      earnedCoinsSpan.innerText = data.earned_coins;
    }
    
    // If the user has discovered a clue, show it
    if (data.show_clue) {
      clueText.innerText = data.clue;
      clueModal.style.display = 'flex';
    }
  })
  .catch(err => console.error('Error saving score:', err));
}

// Close the clue modal when the button is clicked
clueCloseBtn.addEventListener('click', () => {
  clueModal.style.display = 'none';
});

// Also close the modal if the user clicks outside of it
clueModal.addEventListener('click', (event) => {
  if (event.target === clueModal) {
    clueModal.style.display = 'none';
  }
});