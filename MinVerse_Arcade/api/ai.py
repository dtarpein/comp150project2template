import openai
import json
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

def trivia():
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "Generate a random trivia question along with its answer. "
                        "Return a valid JSON object with two keys: 'question' and 'answer'. "
                        "Make the question interesting but not overly difficult. "
                        "Do not include any additional text."
                    )
                },
            ],
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()

        # Try parsing the JSON response
        try:
            data = json.loads(content)
            if 'question' in data and 'answer' in data:
                return data
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract data using string manipulation
            try:
                content = content.replace("```json", "").replace("```", "").strip()
                data = json.loads(content)
                if 'question' in data and 'answer' in data:
                    return data
            except:
                pass
                
        # Fallback to default response
        return {"question": "What is the capital of France?", "answer": "Paris"}
    except Exception as e:
        print(f"API Error: {str(e)}")
        return {"question": "API Error", "answer": "Please try again later"}
