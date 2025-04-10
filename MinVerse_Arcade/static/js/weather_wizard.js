document.getElementById('get-weather').onclick = () => {
  const city = document.getElementById('city-input').value.trim();
  if (!city) {
    alert('Please enter a city name');
    return;
  }
  
  const resultElement = document.getElementById('weather-result');
  resultElement.innerText = 'Loading...';
  
  // Disable button while loading
  const button = document.getElementById('get-weather');
  button.disabled = true;
  
  fetch(`/api/weather?city=${encodeURIComponent(city)}`)
    .then(res => res.json())
    .then(data => {
      if (data.temperature === 'N/A') {
        resultElement.innerText = `Error: ${data.weather}`;
      } else {
        // Create a more detailed weather display
        resultElement.innerHTML = `
          <div class="weather-card">
            <div class="weather-city">${data.city}</div>
            <div class="weather-temp">${data.temperature}°F</div>
            <div class="weather-desc">${data.weather}</div>
            <div class="weather-details">
              <div class="weather-detail">Humidity: ${data.humidity}%</div>
              <div class="weather-detail">Wind: ${data.wind} mph</div>
            </div>
          </div>
        `;
        
        // Play weather sound based on description
        if (data.weather.includes('rain') || data.weather.includes('drizzle')) {
          playSound('rain');
        } else if (data.weather.includes('snow')) {
          playSound('snow');
        } else if (data.weather.includes('thunder')) {
          playSound('thunder');
        } else if (data.temperature < 32) {
          playSound('cold');
        } else if (data.temperature > 85) {
          playSound('hot');
        } else {
          playSound('weather');
        }
      }
      
      // Re-enable button
      button.disabled = false;
      
      // Check if a clue was discovered
      if (data.discovered_clue) {
        // Show clue modal
        showClueModal(data.clue_text, data.earned_coins);
      }
    })
    .catch(err => {
      resultElement.innerText = 'An error occurred. Please try again.';
      console.error('Weather API error:', err);
      
      // Re-enable button
      button.disabled = false;
    });
};

// Also allow Enter key to submit
document.getElementById('city-input').addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    document.getElementById('get-weather').click();
  }
});

// Add suggestions for cold cities to discover the clue
document.addEventListener('DOMContentLoaded', () => {
  const suggestionsDiv = document.createElement('div');
  suggestionsDiv.className = 'city-suggestions';
  suggestionsDiv.innerHTML = `
    <p>Try these cities:</p>
    <div class="suggestion-buttons">
      <button class="suggestion-btn">Anchorage</button>
      <button class="suggestion-btn">Moscow</button>
      <button class="suggestion-btn">Stockholm</button>
      <button class="suggestion-btn">Helsinki</button>
      <button class="suggestion-btn">Reykjavik</button>
    </div>
  `;
  
  // Style the suggestions
  suggestionsDiv.style.marginTop = '20px';
  suggestionsDiv.style.textAlign = 'center';
  
  // Insert after the result element
  const resultElement = document.getElementById('weather-result');
  resultElement.parentNode.insertBefore(suggestionsDiv, resultElement.nextSibling);
  
  // Add event listeners to suggestion buttons
  document.querySelectorAll('.suggestion-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('city-input').value = btn.textContent;
      document.getElementById('get-weather').click();
    });
  });
});

// Add CSS styling for the weather display
document.addEventListener('DOMContentLoaded', () => {
  const style = document.createElement('style');
  style.textContent = `
    .weather-card {
      background-color: rgba(0, 0, 0, 0.3);
      border-radius: 10px;
      padding: 20px;
      margin-top: 20px;
      text-align: center;
    }
    
    .weather-city {
      font-size: 1.5em;
      font-weight: bold;
      margin-bottom: 10px;
    }
    
    .weather-temp {
      font-size: 2.5em;
      font-weight: bold;
      margin-bottom: 10px;
    }
    
    .weather-desc {
      font-size: 1.2em;
      margin-bottom: 15px;
      text-transform: capitalize;
    }
    
    .weather-details {
      display: flex;
      justify-content: space-around;
      margin-top: 10px;
    }
    
    .weather-detail {
      font-size: 1em;
    }
    
    .suggestion-buttons {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 10px;
      margin-top: 10px;
    }
    
    .suggestion-btn {
      background-color: rgba(0, 184, 148, 0.7);
      border: none;
      padding: 5px 10px;
      border-radius: 5px;
      cursor: pointer;
      color: white;
    }
    
    .suggestion-btn:hover {
      background-color: rgba(0, 184, 148, 1);
    }
  `;
  
  document.head.appendChild(style);
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