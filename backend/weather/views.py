import requests
import os
import json
from django.shortcuts import render
from dotenv import load_dotenv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt





load_dotenv()  # Load API key from .env file
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

def location_page(request):
    """Renders the HTML page with location button"""
    return render(request, "weather/location.html")

@csrf_exempt  # Disable CSRF for testing (use proper CSRF handling in production)
def get_weather(request):
    """Receives latitude & longitude and returns weather info."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            latitude = data.get("lat")
            longitude = data.get("lon")

            if not latitude or not longitude:
                return JsonResponse({"status": "error", "message": "Missing coordinates"}, status=400)

            # Fetch weather data
            weather_url = f'https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={WEATHER_API_KEY}&units=metric'
            response = requests.get(weather_url)

            print(response.json())
            if response.status_code == 200:
                weather_data = response.json()
                weather = {
                    'city': weather_data.get('name', 'Unknown'),
                    'temperature': weather_data['main']['temp'],
                    'description': weather_data['weather'][0]['description'],
                    'icon': weather_data['weather'][0]['icon']
                }
                return JsonResponse({"status": "success", "weather": weather})
            else:
                return JsonResponse({"status": "error", "message": "Could not fetch weather"}, status=500)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)




# def index(request):
#     load_dotenv()
#     api_key = os.getenv('WEATHER_API_KEY')
#     url = f'https://api.openweathermap.org/data/2.5/forecast?lat=57&lon=-2.15&appid={api_key}&units=metric'
#     print(url)

#     response = requests.get(url)
#     if response.status_code == 200:
#         city_weather = response.json() #request the API data and convert the JSON to Python data types
#         print(city_weather) #temporarily view output
#         weather = {
#             'city': city_weather['city']['name'],
#             'temperature': city_weather['list'][0]['main']['temp'],
#             'description': city_weather['list'][0]['weather'][0]['description'],
#             'icon': city_weather['list'][0]['weather'][0]['icon']
#         }
#     else:
#         weather = {
#             'city': 'N/A',
#             'temperature': 'N/A',
#             'description': 'N/A',
#             'icon': 'N/A'
#         }
#     return render(request, 'weather/index.html', {'weather': weather})
