import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_weather(city):
    api_key = os.getenv('WEATHER_API_KEY')
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=imperial&appid={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        
        # Check if the request was successful
        if response.status_code != 200:
            return {
                'city': city, 
                'temperature': 'N/A', 
                'weather': f'Error: {response.status_code}'
            }
            
        data = response.json()
        if data.get('cod') != 200:
            return {
                'city': city, 
                'temperature': 'N/A', 
                'weather': data.get('message', 'Unknown error')
            }
            
        return {
            'city': data['name'],  # Use the returned city name to handle capitalization
            'temperature': round(data['main']['temp']),  # Round to nearest whole number
            'weather': data['weather'][0]['description'],
            'humidity': data['main']['humidity'],
            'wind': data['wind']['speed']
        }
    except requests.exceptions.Timeout:
        return {'city': city, 'temperature': 'N/A', 'weather': 'Request timed out'}
    except requests.exceptions.ConnectionError:
        return {'city': city, 'temperature': 'N/A', 'weather': 'Connection error'}
    except Exception as e:
        print(f"Weather API error: {str(e)}")
        return {'city': city, 'temperature': 'N/A', 'weather': 'API Error'}
