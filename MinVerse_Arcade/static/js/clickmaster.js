let clicks = 0;
document.getElementById('click-btn').onclick = () => {
  clicks++;
  document.getElementById('counter').innerText = clicks;
  let sound = new Audio('/static/media/sounds/click.mp3');
  sound.play();
};
