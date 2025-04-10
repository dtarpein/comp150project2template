/**
 * Boss Battle - The final encounter with NEXUS
 * 
 * This script handles the chat interface for the final boss battle,
 * allowing players to use their discovered clues to defeat NEXUS.
 */

document.addEventListener('DOMContentLoaded', () => {
    const cluePanel = document.getElementById('clue-panel');
    const clueToggle = document.getElementById('clue-toggle');
    const conversationArea = document.getElementById('conversation');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const nexusContainer = document.getElementById('nexus-container');
    const weaknessIndicators = document.querySelectorAll('.weakness-indicator');
    
    // Track whether NEXUS is currently responding
    let isProcessing = false;
    
    // Initialize glitch effect
    const glitch = new Glitch(nexusContainer);
    
    // Toggle clue panel visibility
    if (clueToggle) {
      clueToggle.addEventListener('click', () => {
        cluePanel.classList.toggle('open');
        
        // Update button text
        const isOpen = cluePanel.classList.contains('open');
        clueToggle.textContent = isOpen ? 'Hide Clues' : 'Show Clues';
      });
    }
    
    // Send message to NEXUS
    if (sendButton && userInput) {
      sendButton.addEventListener('click', sendMessage);
      userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendMessage();
        }
      });
    }
    
    // Function to send user message to NEXUS
    function sendMessage() {
      // Don't allow sending empty messages or while processing
      const message = userInput.value.trim();
      if (!message || isProcessing) return;
      
      // Add user message to conversation
      addMessageToConversation('user', message);
      
      // Clear input
      userInput.value = '';
      
      // Disable input while processing
      isProcessing = true;
      userInput.disabled = true;
      sendButton.disabled = true;
      
      // Show typing indicator
      addTypingIndicator();
      
      // Send message to server
      fetch('/api/nexus_chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message })
      })
      .then(res => res.json())
      .then(data => {
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add NEXUS response to conversation
        addMessageToConversation('nexus', data.message);
        
        // Handle weakness found
        if (data.weakness_found) {
          triggerWeaknessFound(data.weaknesses_found);
        }
        
        // Handle victory
        if (data.victory) {
          triggerVictory();
          
          // Redirect after delay
          setTimeout(() => {
            window.location.href = data.redirect;
          }, 8000);
        }
        
        // Re-enable input
        isProcessing = false;
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.focus();
      })
      .catch(err => {
        console.error('Error sending message:', err);
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add error message
        addMessageToConversation('system', 'Connection error. Please try again.');
        
        // Re-enable input
        isProcessing = false;
        userInput.disabled = false;
        sendButton.disabled = false;
      });
    }
    
    // Add message to conversation area
    function addMessageToConversation(role, content) {
      const messageDiv = document.createElement('div');
      messageDiv.className = `message ${role}-message`;
      
      if (role === 'nexus') {
        messageDiv.innerHTML = formatNexusMessage(content);
      } else {
        messageDiv.textContent = content;
      }
      
      conversationArea.appendChild(messageDiv);
      
      // Scroll to bottom
      conversationArea.scrollTop = conversationArea.scrollHeight;
      
      // Play appropriate sound
      if (role === 'user') {
        playSound('message-sent');
      } else if (role === 'nexus') {
        playSound('nexus-response');
      }
    }
    
    // Format NEXUS message with glitchy text effects
    function formatNexusMessage(message) {
      // Replace error indicators with glitchy spans
      message = message.replace(/ERR-ERROR|WARNING|CRITICAL|SYS-SYSTEM/g, 
        match => `<span class="glitch-text">${match}</span>`);
      
      // Add digital distortion to stuttering text
      message = message.replace(/(\w)-\1/g, 
        match => `<span class="stutter-text">${match}</span>`);
      
      return message;
    }
    
    // Add typing indicator to show NEXUS is "thinking"
    function addTypingIndicator() {
      const typingDiv = document.createElement('div');
      typingDiv.className = 'typing-indicator';
      typingDiv.innerHTML = '<span></span><span></span><span></span>';
      conversationArea.appendChild(typingDiv);
      
      // Scroll to bottom
      conversationArea.scrollTop = conversationArea.scrollHeight;
    }
    
    // Remove typing indicator
    function removeTypingIndicator() {
      const typingIndicator = conversationArea.querySelector('.typing-indicator');
      if (typingIndicator) {
        typingIndicator.remove();
      }
    }
    
    // Trigger effects when a weakness is found
    function triggerWeaknessFound(weaknessCount) {
      // Play weakness sound
      playSound('weakness-found');
      
      // Activate the appropriate weakness indicator
      if (weaknessCount > 0 && weaknessCount <= weaknessIndicators.length) {
        weaknessIndicators[weaknessCount - 1].classList.add('active');
      }
      
      // Trigger heavy glitch effect
      glitch.triggerHeavyGlitch();
    }
    
    // Trigger victory effects
    function triggerVictory() {
      // Play victory sound
      playSound('victory');
      
      // Add victory class to NEXUS container
      nexusContainer.classList.add('collapsing');
      
      // Activate all weakness indicators
      weaknessIndicators.forEach(indicator => {
        indicator.classList.add('active');
      });
      
      // Trigger collapse glitch effect
      glitch.triggerCollapseGlitch();
      
      // Disable input permanently
      userInput.disabled = true;
      sendButton.disabled = true;
    }
    
    // Play sound effects
    function playSound(soundName) {
      try {
        const audio = new Audio(`/static/media/sounds/${soundName}.mp3`);
        audio.play().catch(err => console.log('Audio playback error:', err));
      } catch (e) {
        console.error('Error playing sound:', e);
      }
    }
  });
  
  /**
   * Glitch effect class for NEXUS visual distortions
   */
  class Glitch {
    constructor(element) {
      this.element = element;
      this.glitchInterval = null;
      this.glitchIntensity = 0;
      
      // Start subtle glitch effect
      this.startSubtleGlitch();
    }
    
    startSubtleGlitch() {
      // Clear any existing interval
      if (this.glitchInterval) {
        clearInterval(this.glitchInterval);
      }
      
      // Set low intensity
      this.glitchIntensity = 1;
      
      // Start interval
      this.glitchInterval = setInterval(() => {
        this.applyGlitchEffect();
      }, 5000); // Subtle glitch every 5 seconds
    }
    
    triggerHeavyGlitch() {
      // Clear subtle glitch interval
      clearInterval(this.glitchInterval);
      
      // Set high intensity
      this.glitchIntensity = 10;
      
      // Apply heavy glitch multiple times
      let glitchCount = 0;
      const maxGlitches = 8;
      
      const heavyGlitchInterval = setInterval(() => {
        this.applyGlitchEffect();
        glitchCount++;
        
        if (glitchCount >= maxGlitches) {
          clearInterval(heavyGlitchInterval);
          
          // Return to subtle glitching
          setTimeout(() => {
            this.startSubtleGlitch();
          }, 1000);
        }
      }, 200);
    }
    
    triggerCollapseGlitch() {
      // Clear any existing interval
      clearInterval(this.glitchInterval);
      
      // Set maximum intensity
      this.glitchIntensity = 20;
      
      // Apply intense glitches continuously
      this.glitchInterval = setInterval(() => {
        this.applyGlitchEffect();
      }, 100);
    }
    
    applyGlitchEffect() {
      // Apply random CSS transformations based on intensity
      const skewX = (Math.random() - 0.5) * this.glitchIntensity;
      const skewY = (Math.random() - 0.5) * this.glitchIntensity;
      const translateX = (Math.random() - 0.5) * this.glitchIntensity * 2;
      const translateY = (Math.random() - 0.5) * this.glitchIntensity * 2;
      const scale = 1 + (Math.random() - 0.5) * 0.1 * this.glitchIntensity;
      
      this.element.style.transform = `
        skew(${skewX}deg, ${skewY}deg)
        translate(${translateX}px, ${translateY}px)
        scale(${scale})
      `;
      
      // Add color filter distortion
      if (Math.random() < 0.3 * (this.glitchIntensity / 10)) {
        const hueRotate = Math.floor(Math.random() * 360);
        this.element.style.filter = `hue-rotate(${hueRotate}deg) saturate(2)`;
      } else {
        this.element.style.filter = '';
      }
      
      // Reset after short delay
      setTimeout(() => {
        this.element.style.transform = '';
        this.element.style.filter = '';
      }, 150);
    }
  }