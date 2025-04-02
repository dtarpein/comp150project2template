document.getElementById('get-weather').onclick = () => {
    const city = document.getElementById('city-input').value.trim();
    if (!city) {
      alert('Please enter a city name');
      return;
    }
    
    const resultElement = document.getElementById('weather-result');
    resultElement.innerText = 'Loading...';
    
    fetch(`/api/weather?city=${encodeURIComponent(city)}`)
      .then(res => res.json())
      .then(data => {
        if (data.temperature === 'N/A') {
          resultElement.innerText = `Error: ${data.weather}`;
        } else {
          resultElement.innerText = `${data.city}: ${data.temperature}°F, ${data.weather}`;
        }
      })
      .catch(err => {
        resultElement.innerText = 'An error occurred. Please try again.';
        console.error('Weather API error:', err);
      });
  };
  
  // Also allow Enter key to submit
  document.getElementById('city-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      document.getElementById('get-weather').click();
    }
  });
  