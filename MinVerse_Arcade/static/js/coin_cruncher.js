/**
 * Coin Cruncher - A mischievous enemy that steals coins from the player
 * 
 * This class creates a character that randomly appears to steal coins.
 * Players need to click rapidly to defeat it before it steals their coins.
 */

// Initialize the coin cruncher when document is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize for logged-in users
    if (document.querySelector('.navbar a[href="/logout"]')) {
      window.coinCruncher = new CoinCruncher();
    }
  });
  class CoinCruncher {
    constructor() {
      this.isActive = false;
      this.element = null;
      this.appearInterval = null;
      this.disappearTimeout = null;
      this.clickHandler = null;
      this.stealer = null;
      this.clickCounter = 0;
      this.clickThreshold = 10; // Clicks needed to defeat the cruncher
      this.stealAmount = 0;
      
      // Create HTML element
      this.createCruncherElement();
      
      // Start the random appearance schedule
      this.scheduleNextAppearance();
    }
    
    createCruncherElement() {
      // Create the main container
      this.element = document.createElement('div');
      this.element.className = 'coin-cruncher';
      this.element.innerHTML = `
        <div class="coin-cruncher-head"></div>
        <div class="coin-cruncher-body">
          <div class="coin-cruncher-eyes">
            <div class="eye left"></div>
            <div class="eye right"></div>
          </div>
          <div class="coin-cruncher-mouth"></div>
        </div>
        <div class="coin-steal-indicator">
          <span class="steal-amount">-10</span>
          <span class="coin-icon">💰</span>
        </div>
        <div class="click-counter">
          <span class="clicks-needed">10</span> clicks to defeat!
        </div>
      `;
      
      // Add the element to the body but hide it initially
      document.body.appendChild(this.element);
      
      // Set up click handler
      this.clickHandler = this.handleClick.bind(this);
    }
    
    scheduleNextAppearance() {
      // Only schedule appearances for logged-in users
      if (!document.querySelector('.navbar a[href="/logout"]')) {
        return;
      }
      
      // Random time between min and max appearance interval (2-5 minutes)
      const minInterval = 30; // For testing, set to 30 seconds
      const maxInterval = 120; // For testing, set to 2 minutes
      // In production you might want to use:
      // const minInterval = 120; // 2 minutes
      // const maxInterval = 300; // 5 minutes
      
      const randomInterval = Math.floor(Math.random() * (maxInterval - minInterval + 1)) + minInterval;
      
      // Schedule next appearance
      this.appearInterval = setTimeout(() => {
        this.appear();
      }, randomInterval * 1000);
    }
    
    appear() {
      // Only appear if not already active and user is logged in
      if (this.isActive || !document.querySelector('.navbar a[href="/logout"]')) {
        this.scheduleNextAppearance();
        return;
      }
      
      // Reset the click counter
      this.clickCounter = 0;
      
      // Calculate amount to steal - random between 5-15 coins
      this.stealAmount = Math.floor(Math.random() * 11) + 5;
      
      // Update the steal amount display
      this.element.querySelector('.steal-amount').textContent = `-${this.stealAmount}`;
      this.element.querySelector('.clicks-needed').textContent = this.clickThreshold;
      
      // Play appearance sound
      this.playSound('cruncher-appear');
      
      // Show the cruncher
      this.isActive = true;
      this.element.style.display = 'block';
      
      // Animate entrance
      setTimeout(() => {
        this.element.classList.add('active');
        
        // Add click handler
        this.element.addEventListener('click', this.clickHandler);
        
        // Schedule automatic disappearance with coin theft if not clicked enough
        this.disappearTimeout = setTimeout(() => {
          this.stealCoins();
        }, 10000); // 10 seconds
      }, 100);
    }
    
    handleClick() {
      // Increment click counter
      this.clickCounter++;
      
      // Play click sound
      this.playSound('click');
      
      // Update the clicks needed display
      const clicksNeeded = Math.max(0, this.clickThreshold - this.clickCounter);
      this.element.querySelector('.clicks-needed').textContent = clicksNeeded;
      
      // Check if clicked enough to defeat
      if (this.clickCounter >= this.clickThreshold) {
        this.defeatCruncher();
      }
    }
    
    defeatCruncher() {
      // Clear the auto-disappear timeout
      if (this.disappearTimeout) {
        clearTimeout(this.disappearTimeout);
      }
      
      // Remove click handler
      this.element.removeEventListener('click', this.clickHandler);
      
      // Play defeat sound
      this.playSound('cruncher-defeat');
      
      // Add defeat class for animation
      this.element.classList.add('defeated');
      
      // Hide after animation
      setTimeout(() => {
        this.element.classList.remove('active', 'defeated');
        this.isActive = false;
        
        setTimeout(() => {
          this.element.style.display = 'none';
          
          // Schedule next appearance
          this.scheduleNextAppearance();
        }, 500);
      }, 1500);
    }
    
    stealCoins() {
      // Clear event listener
      this.element.removeEventListener('click', this.clickHandler);
      
      // Add stealing class for animation
      this.element.classList.add('stealing');
      
      // Play stealing sound
      this.playSound('coin-steal');
      
      // Make API call to steal coins
      fetch('/api/steal_coins', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: this.stealAmount })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          // Update the coins display
          const coinsDisplay = document.querySelector('.top-coin-display .coin-value');
          if (coinsDisplay) {
            coinsDisplay.textContent = data.coins_remaining;
          }
          
          // Show stealing animation
          const stealIndicator = this.element.querySelector('.coin-steal-indicator');
          stealIndicator.classList.add('active');
          
          setTimeout(() => {
            stealIndicator.classList.remove('active');
          }, 2000);
        }
      })
      .catch(err => console.error('Error stealing coins:', err));
      
      // Hide after stealing
      setTimeout(() => {
        this.element.classList.remove('active', 'stealing');
        this.isActive = false;
        
        setTimeout(() => {
          this.element.style.display = 'none';
          
          // Schedule next appearance
          this.scheduleNextAppearance();
        }, 500);
      }, 2500);
    }
    
    playSound(soundName) {
      try {
        const audio = new Audio(`/static/media/sounds/${soundName}.mp3`);
        audio.play().catch(err => console.log('Audio playback error:', err));
      } catch (e) {
        console.error('Error playing sound:', e);
      }
    }
  }