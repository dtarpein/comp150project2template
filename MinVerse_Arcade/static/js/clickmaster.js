let clicks = 0;
const clickBtn = document.getElementById('click-btn');
const clickCount = document.getElementById('click-count');
const coinCount = document.getElementById('coin-count');
const clueModal = document.getElementById('clue-modal');
const clueText = document.getElementById('clue-text');
const clueCloseBtn = document.getElementById('clue-close-btn');
const earnedCoinsSpan = document.getElementById('earned-coins');

// Load user's coins when page loads
window.addEventListener('DOMContentLoaded', () => {
  fetchUserCoins();
  
  // Add a submit button 
  const submitButton = document.createElement('button');
  submitButton.innerText = 'Submit Score';
  submitButton.style.margin = '15px auto';
  submitButton.style.display = 'block';
  submitButton.style.padding = '10px 20px';
  
  // Add the button after the click counter
  document.querySelector('p').after(submitButton);
  
  // Add click handler for submit button
  submitButton.addEventListener('click', () => {
    sendScore(clicks);
  });
});

// Fetch the user's current coins
function fetchUserCoins() {
  fetch('/user/coins')
    .then(res => res.json())
    .then(data => {
      coinCount.innerText = data.coins;
    })
    .catch(err => console.error('Error fetching coins:', err));
}

// Handle clicks on the button
clickBtn.addEventListener('click', () => {
  clicks++;
  clickCount.innerText = clicks;
  
  // Play sound if available
  try {
    const audio = new Audio('/static/media/sounds/click.mp3');
    audio.play().catch(err => {});
  } catch (err) {}

  // Check if we hit exactly 42 clicks
  if (clicks === 42) {
    console.log("Hit 42 clicks, sending score...");
    sendScore(clicks);
  }
});

// Send the score to the server
function sendScore(score) {
  console.log('Sending score:', score);
  
  fetch('/games/clickmaster', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ score: score })
  })
  .then(res => res.json())
  .then(data => {
    console.log('Server response:', data);
    
    // Update coins if earned
    if (data.earned_coins) {
      console.log('Earned coins:', data.earned_coins);
      fetchUserCoins();
      earnedCoinsSpan.innerText = data.earned_coins;
    }
    
    // Show clue if discovered
    if (data.show_clue) {
      console.log('Clue discovered! Text:', data.clue);
      clueText.innerText = data.clue;
      clueModal.style.display = 'flex';
    } else {
      console.log('No clue in response');
    }
  })
  .catch(err => console.error('Error saving score:', err));
}

// Close the clue modal when the button is clicked
if (clueCloseBtn) {
  clueCloseBtn.addEventListener('click', () => {
    clueModal.style.display = 'none';
  });
}

// Also close the modal if the user clicks outside of it
if (clueModal) {
  clueModal.addEventListener('click', (event) => {
    if (event.target === clueModal) {
      clueModal.style.display = 'none';
    }
  });
}