const canvas = document.getElementById('spaceCanvas');
const ctx = canvas.getContext('2d');

let player = { x: 50, y: 180, width: 30, height: 30 };
let obstacles = [];
let gameOver = false;
let score = 0;
let frameCount = 0;

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
      
      // Save score
      fetch('/games/space_dodger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ score: score })
      })
      .then(res => res.json())
      .catch(err => console.error('Error saving score:', err));
      
      // Show game over with restart option
      if (confirm('💥 Game Over! Your score: ' + score + '. Play again?')) {
        restartGame();
      }
      break;
    }
  }
}

function drawScore() {
  ctx.fillStyle = 'white';
  ctx.font = '20px Arial';
  ctx.fillText('Score: ' + score, 10, 30);
}

function gameLoop() {
  if (gameOver) return;
  
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  // Increment score based on survival time
  frameCount++;
  if (frameCount % 10 === 0) {
    score++;
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

// Start the game
gameLoop();
