/**
 * Coin Display - Shows a persistent coin counter across all pages
 */

document.addEventListener('DOMContentLoaded', () => {
    // Only create the coin display for logged-in users
    if (document.querySelector('.navbar a[href="/logout"]')) {
      createCoinDisplay();
      
      // Refresh coin count every 30 seconds
      setInterval(updateCoinCount, 30000);
    }
  });
  
  function createCoinDisplay() {
    // Create the coin display element
    const coinDisplay = document.createElement('div');
    coinDisplay.className = 'top-coin-display';
    coinDisplay.innerHTML = `
      <span class="coin-icon">💰</span>
      <span class="coin-value">0</span>
    `;
    
    // Add to the document
    document.body.appendChild(coinDisplay);
    
    // Initialize with current coin count
    updateCoinCount();
  }
  
  function updateCoinCount() {
    fetch('/user/coins')
      .then(res => res.json())
      .then(data => {
        const coinValueElement = document.querySelector('.top-coin-display .coin-value');
        if (coinValueElement) {
          // If the value has changed, animate the update
          const currentValue = parseInt(coinValueElement.textContent, 10);
          if (currentValue !== data.coins) {
            animateCoinChange(coinValueElement, currentValue, data.coins);
          }
        }
      })
      .catch(err => console.error('Error fetching coin count:', err));
  }
  
  function animateCoinChange(element, oldValue, newValue) {
    // Add appropriate animation class
    if (oldValue < newValue) {
      element.classList.add('coin-increase');
      playSound('coin-earned');
    } else if (oldValue > newValue) {
      element.classList.add('coin-decrease');
      playSound('coin-lost');
    }
    
    // Update the value
    element.textContent = newValue;
    
    // Remove animation class after animation completes
    setTimeout(() => {
      element.classList.remove('coin-increase', 'coin-decrease');
    }, 1000);
  }
  
  function playSound(soundName) {
    try {
      const audio = new Audio(`/static/media/sounds/${soundName}.mp3`);
      audio.play().catch(err => console.log('Audio playback error:', err));
    } catch (e) {
      console.error('Error playing sound:', e);
    }
  }