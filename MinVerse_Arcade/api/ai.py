import openai
import json
import os
import time
import random
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

def trivia():
    # Generate a random value and current timestamp to ensure uniqueness
    random_value = random.random()
    current_timestamp = int(time.time())
    
    system_message = (
        "Generate a unique, random trivia question along with its answer. "
        "Ensure the question is interesting, not overly difficult, and not a repeat. "
        "Return a valid JSON object with two keys: 'question' and 'answer'. "
        f"Random seed: {random_value}, Timestamp: {current_timestamp}."
    )
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": system_message}],
            temperature=0.9  # Increase randomness for more varied output
        )
        content = response.choices[0].message.content.strip()
        
        # Try parsing the JSON response
        try:
            data = json.loads(content)
            if 'question' in data and 'answer' in data:
                return data
        except json.JSONDecodeError:
            # If JSON parsing fails, try to clean up the content and parse again
            try:
                content = content.replace("```json", "").replace("```", "").strip()
                data = json.loads(content)
                if 'question' in data and 'answer' in data:
                    return data
            except:
                pass
                
        # Fallback to a default response if parsing fails
        return {"question": "What is the capital of France?", "answer": "Paris"}
    except Exception as e:
        print(f"API Error: {str(e)}")
        return {"question": "API Error", "answer": "Please try again later"}

