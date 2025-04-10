const canvas = document.getElementById('spaceCanvas');
const ctx = canvas.getContext('2d');

let player = { x: 50, y: 180, width: 30, height: 30 };
let obstacles = [];
let gameOver = false;
let score = 0;
let frameCount = 0;
let highScore = 0;

function drawPlayer() {
  ctx.fillStyle = 'lime';
  ctx.fillRect(player.x, player.y, player.width, player.height);
}

function drawObstacle(obs) {
  ctx.fillStyle = 'red';
  ctx.fillRect(obs.x, obs.y, obs.width, obs.height);
}

function updateObstacles() {
  // Increase obstacle spawn rate as score increases
  const spawnRate = Math.max(0.01, 0.04 - (score / 1000));
  
  if (Math.random() < spawnRate) {
    obstacles.push({ 
      x: canvas.width, 
      y: Math.random() * (canvas.height - 30), 
      width: 20, 
      height: 30 
    });
  }
  
  obstacles.forEach(o => {
    // Increase speed as score increases
    const speed = 3 + Math.floor(score / 200);
    o.x -= speed;
  });
  
  // Remove obstacles that have moved off screen
  obstacles = obstacles.filter(o => o.x + o.width > 0);
}

function checkCollision() {
  for (let o of obstacles) {
    if (
      player.x < o.x + o.width &&
      player.x + player.width > o.x &&
      player.y < o.y + o.height &&
      player.y + player.height > o.y
    ) {
      gameOver = true;
      
      // Play collision sound
      playSound('explosion');
      
      // Save score
      fetch('/games/space_dodger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ score: score })
      })
      .then(res => res.json())
      .then(data => {
        console.log(data.message);
        
        // Check if coins were earned
        if (data.earned_coins) {
          showNotification(`You earned ${data.earned_coins} coins!`);
        }
        
        // If a clue was discovered, show it
        if (data.show_clue) {
          setTimeout(() => {
            showClueModal(data.clue, data.earned_coins);
          }, 1000);
        } else {
          // Show game over with restart option after a short delay
          setTimeout(() => {
            if (confirm(`💥 Game Over! Your score: ${score}. Play again?`)) {
              restartGame();
            }
          }, 500);
        }
      })
      .catch(err => {
        console.error('Error saving score:', err);
        
        // Show game over with restart option
        setTimeout(() => {
          if (confirm(`💥 Game Over! Your score: ${score}. Play again?`)) {
            restartGame();
          }
        }, 500);
      });
      
      break;
    }
  }
}

function drawScore() {
  ctx.fillStyle = 'white';
  ctx.font = '20px Arial';
  ctx.fillText('Score: ' + score, 10, 30);
  
  // Also draw high score if it exists
  if (highScore > 0) {
    ctx.fillText('High Score: ' + highScore, canvas.width - 160, 30);
  }
}

function gameLoop() {
  if (gameOver) return;
  
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  // Increment score based on survival time
  frameCount++;
  if (frameCount % 10 === 0) {
    score++;
    
    // Check for high score achievement
    if (score > highScore) {
      highScore = score;
    }
  }
  
  drawScore();
  drawPlayer();
  updateObstacles();
  obstacles.forEach(drawObstacle);
  checkCollision();
  
  requestAnimationFrame(gameLoop);
}

function restartGame() {
  player = { x: 50, y: 180, width: 30, height: 30 };
  obstacles = [];
  gameOver = false;
  score = 0;
  frameCount = 0;
  gameLoop();
}

document.addEventListener('keydown', e => {
  if (gameOver) return;
  
  const playerSpeed = 20;
  
  if (e.key === 'ArrowUp' && player.y > 0) {
    player.y -= playerSpeed;
  } else if (e.key === 'ArrowDown' && player.y + player.height < canvas.height) {
    player.y += playerSpeed;
  } else if (e.key === 'ArrowLeft' && player.x > 0) {
    player.x -= playerSpeed;
  } else if (e.key === 'ArrowRight' && player.x + player.width < canvas.width) {
    player.x += playerSpeed;
  }
});

// Add a restart button
const restartBtn = document.createElement('button');
restartBtn.innerText = 'Restart Game';
restartBtn.onclick = restartGame;
canvas.parentNode.insertBefore(restartBtn, canvas.nextSibling);

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
      // After closing clue modal, ask if they want to play again
      if (confirm(`Game Over! Your score: ${score}. Play again?`)) {
        restartGame();
      }
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
  document.getElementById('earned-coins-text').textContent = earnedCoins || 0;
  modal.style.display = 'flex';
  
  // Play clue sound
  playSound('clue-discovered');
}

// Start the game
gameLoop();