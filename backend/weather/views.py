import requests
import os
import json
import openai
from django.shortcuts import render
from dotenv import load_dotenv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')



def get_activity_suggestions(weather, location):
    prompt = f"""
    You are an assistant that provides structured activity suggestions. 
    Provide exactly 10 outdoor activities suitable for {weather} weather in {location}. 

    Return the response **strictly** in JSON format as a list of objects. 
    Each object must have:
    - "place": A specific location where the activity can be done (e.g., "Central Park" or "Beach near Downtown").
    - "activity": A full sentence describing the activity (e.g., "Go for a relaxing jog at Central Park").

    **Output ONLY valid JSON** with no extra text, explanation, or formatting.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        response_text = response['choices'][0]['message']['content'].strip()
        
        # Debug: Print the raw response to inspect issues
        print("Raw OpenAI Response:", response_text)
        
        # Attempt to parse JSON
        activity_data = json.loads(response_text)

        # Ensure response is correctly formatted as a list of dicts with "place" and "activity"
        if isinstance(activity_data, list) and all("place" in item and "activity" in item for item in activity_data):
            return activity_data
        else:
            print("Unexpected response format:", activity_data)
            return []
    
    except (json.JSONDecodeError, KeyError) as e:
        print("Error parsing JSON:", e)
        return []



def location_page(request):
    """Renders the HTML page with location button"""
    google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    return render(request, "weather/location.html", {"google_maps_api_key": google_maps_api_key})

@csrf_exempt  # Disable CSRF for testing (use proper CSRF handling in production)
def get_weather(request):
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

            # print(response.json())
            if response.status_code == 200:
                weather_data = response.json()
                weather = {
                    'city': weather_data.get('name', 'Unknown'),
                    'temperature': weather_data['main']['temp'],
                    'description': weather_data['weather'][0]['description'],                }
                google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
                # activities = get_activity_suggestions(weather['description'], time_of_day, weather['city'])
                # activities = get_activity_suggestions(weather['description'], weather['city'])
                activities = [{'place': 'Sidi Ma’rouf Park', 'activity': 'Take a leisurely stroll and enjoy the greenery in Sidi Ma’rouf Park.'}, {'place': 'Parc de la Ligue Arabe', 'activity': 'Have a picnic and soak up the sun in Parc de la Ligue Arabe.'}, {'place': 'Bouskoura Forest', 'activity': 'Go for a hike and explore the trails in Bouskoura Forest.'}, {'place': 'Mohammedia Beach', 'activity': 'Relax on the sandy shores and take a dip in the sea at Mohammedia Beach.'}, {'place': 'Anfa Place', 'activity': 'Enjoy a leisurely bike ride along the waterfront at Anfa Place.'}, {'place': 'Ain Diab Beach', 'activity': 'Catch some waves or simply unwind on the picturesque Ain Diab Beach.'}, {'place': 'Tamaris Beach', 'activity': 'Partake in some beach volleyball or simply bask in the sun at Tamaris Beach.'}, {'place': 'The Corniche', 'activity': 'Take a scenic walk along The Corniche and enjoy stunning views of the coastline.'}, {'place': 'La Sqala', 'activity': 'Have a relaxing outdoor meal and enjoy the historic surroundings at La Sqala.'}, {'place': 'Mohammed V Square', 'activity': 'Join a friendly game of soccer or frisbee at Mohammed V Square.'}]
                # print(activities)
                response_data = ({
                    "status": "success", 
                    "weather": weather,
                    "activities": activities
                    })
                print(json.dumps(response_data, indent=4))
                return JsonResponse(response_data)
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
