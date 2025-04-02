let currentQuestion = null;

document.getElementById('new-question').onclick = () => {
  const questionEl = document.getElementById('question');
  questionEl.innerText = 'Loading...';
  document.getElementById('answer').innerText = '';
  
  fetch('/api/trivia')
    .then(res => res.json())
    .then(data => {
      currentQuestion = data;
      questionEl.innerText = data.question;
    })
    .catch(err => {
      questionEl.innerText = 'Error loading question. Please try again.';
      console.error('Trivia API error:', err);
    });
};

document.getElementById('show-answer').onclick = () => {
  const answerEl = document.getElementById('answer');
  
  if (!currentQuestion) {
    answerEl.innerText = 'Please get a question first!';
    return;
  }
  
  answerEl.innerText = currentQuestion.answer;
};

// Load a question when the page first loads
window.onload = () => {
  document.getElementById('new-question').click();
};
