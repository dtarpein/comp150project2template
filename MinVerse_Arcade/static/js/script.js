const button = document.getElementById('myButton');
const clickCount = document.getElementById('clickCount');

button.addEventListener('click', function() {
  axios.post('/increment')
    .then(function(response) {
      clickCount.textContent = response.data.count;
    })
    .catch(function(error) {
      console.log(error);
    });
});

const inputText = document.getElementById('inputText');
const flipButton = document.getElementById('flipButton');
const result = document.getElementById('result');

flipButton.addEventListener('click', function() {
  const text = inputText.value;
  axios.post('/flip_case', { text: text })
    .then(function(response) {
      result.textContent = response.data.flipped_text;
    })
    .catch(function(error) {
      console.log(error);
    });
});