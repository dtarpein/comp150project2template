const emojis = ['🍕', '🚀', '🎮', '🐶', '🌈', '🎧', '🧠', '🍩'];
let cards = [...emojis, ...emojis]; // duplicates for pairs
let firstCard = null;
let secondCard = null;
let lockBoard = false;
let matches = 0;
let attempts = 0;

function shuffle(array) {
  array.sort(() => 0.5 - Math.random());
}

function createCard(emoji) {
  const card = document.createElement('div');
  card.classList.add('card');
  card.dataset.emoji = emoji;

  const front = document.createElement('div');
  front.classList.add('front');
  front.textContent = emoji;

  const back = document.createElement('div');
  back.classList.add('back');
  back.textContent = '❓';

  card.appendChild(front);
  card.appendChild(back);

  card.addEventListener('click', () => {
    if (lockBoard || card === firstCard || card.classList.contains('matched')) return;

    card.classList.add('flipped');
    if (!firstCard) {
      firstCard = card;
      return;
    }

    secondCard = card;
    lockBoard = true;
    attempts++;
    document.getElementById('attempts').innerText = attempts;

    if (firstCard.dataset.emoji === secondCard.dataset.emoji) {
      firstCard.classList.add('matched');
      secondCard.classList.add('matched');
      matches++;
      document.getElementById('matches').innerText = matches;
      resetBoard();
      playSound('match');
    } else {
      playSound('fail');
      setTimeout(() => {
        firstCard.classList.remove('flipped');
        secondCard.classList.remove('flipped');
        resetBoard();
      }, 800);
    }
  });

  return card;
}

function resetBoard() {
  [firstCard, secondCard] = [null, null];
  lockBoard = false;
}

function playSound(type) {
  let soundPath = type === 'match' ? 'match.mp3' : 'fail.mp3';
  let audio = new Audio(`/static/media/sounds/${soundPath}`);
  audio.play();
}

// Initialization
const gameBoard = document.getElementById('memory-game');
shuffle(cards);
cards.forEach(emoji => {
  const card = createCard(emoji);
  gameBoard.appendChild(card);
});
