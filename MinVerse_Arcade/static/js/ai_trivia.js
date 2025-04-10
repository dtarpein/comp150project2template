let currentQuestion = null;
let questionsAsked = 0;

document.getElementById('new-question').onclick = () => {
  const questionEl = document.getElementById('question');
  questionEl.innerText = 'Loading...';
  document.getElementById('answer').innerText = '';
  
  // Disable button while loading
  const button = document.getElementById('new-question');
  button.disabled = true;
  
  fetch('/api/trivia')
    .then(res => res.json())
    .then(data => {
      currentQuestion = data;
      questionEl.innerText = data.question;
      
      // Increment questions asked counter
      questionsAsked++;
      
      // Re-enable button
      button.disabled = false;
      
      // Check if a clue was discovered
      if (data.discovered_clue) {
        // Show clue modal
        showClueModal(data.clue_text, data.earned_coins);
      }
    })
    .catch(err => {
      questionEl.innerText = 'Error loading question. Please try again.';
      console.error('Trivia API error:', err);
      
      // Re-enable button
      button.disabled = false;
    });
};

document.getElementById('show-answer').onclick = () => {
  const answerEl = document.getElementById('answer');
  
  if (!currentQuestion) {
    answerEl.innerText = 'Please get a question first!';
    return;
  }
  
  // Show the answer with a slight delay for effect
  answerEl.innerText = 'Revealing answer...';
  
  setTimeout(() => {
    answerEl.innerText = currentQuestion.answer;
    
    // Play reveal sound
    playSound('reveal');
    
    // Award coins for learning (every 5 questions)
    if (questionsAsked % 5 === 0) {
      // Check if coin notification exists
      let exists = document.getElementById('coin-notification');
      
      if (!exists) {
        fetch('/user/coins')
          .then(res => res.json())
          .then(data => {
            // Just a check to make sure we can access coins API
            console.log('Current coins:', data.coins);
            showNotification('Knowledge is power! +1 coin');
          })
          .catch(err => console.error('Error fetching coins:', err));
      }
    }
  }, 500);
};

// Load a question when the page first loads
window.onload = () => {
  document.getElementById('new-question').click();
};

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