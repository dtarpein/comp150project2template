document.getElementById('flip-btn').onclick = () => {
    const input = document.getElementById('user-input').value;
    const flipped = input.split('').map(c =>
      c === c.toLowerCase() ? c.toUpperCase() : c.toLowerCase()
    ).join('');
    document.getElementById('result').innerText = flipped;
  };
  