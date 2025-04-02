let clicks = 0;
const clickBtn = document.getElementById('click-btn');
const clickCount = document.getElementById('click-count');

clickBtn.onclick = () => {
  clicks++;
  clickCount.innerText = clicks;
  
  // Play sound with error handling
  const audio = new Audio('/static/media/sounds/click.mp3');
  audio.play().catch(err => console.log('Audio playback error:', err));

  // Send score to backend after 10 clicks (example threshold)
  if (clicks % 10 === 0) {
    fetch('/games/clickmaster', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ score: clicks })
    })
    .then(res => res.json())
    .then(data => console.log(data.message))
    .catch(err => console.error('Error saving score:', err));
  }
};
