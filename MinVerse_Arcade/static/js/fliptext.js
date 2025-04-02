document.getElementById('flip-button').onclick = () => {
    const input = document.getElementById('flip-input').value;
    const flipped = input
      .split('')
      .map(c => c === c.toLowerCase() ? c.toUpperCase() : c.toLowerCase())
      .join('');
    document.getElementById('flip-output').innerText = flipped;
  };
  