import requests
import os
import json
import openai
import re
from django.shortcuts import render
from dotenv import load_dotenv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

seen_places = set()

@csrf_exempt
def get_new_suggestion(request):
    if request.method == "POST":
        data = json.loads(request.body)
        dismissed_activity = data.get("dismissed_activity")
        place = data.get("place")

        if "seen_activities" in request.session:
            request.session["seen_activities"] = [
                place for place in request.session["seen_activities"] if place != dismissed_activity
            ]

        # Fetch new activities, excluding dismissed ones
        weather = request.session.get("weather_description")
        time_of_day = request.session.get("time_of_day")
        city = request.session.get("city")

        new_activities = get_activity_suggestions(weather, time_of_day, city, dismissed_activity)
        available_activities = []
        for activity in new_activities:
            place_name = activity['place']
            opening_hours = get_place_opening_hours(place_name)
            if opening_hours and is_place_open(opening_hours):
                available_activities.append(activity)
        filtered_activities = [
            activity for activity in available_activities if activity["place"] not in request.session["seen_activities"]
        ]

        if filtered_activities:
            request.session["seen_activities"].append(filtered_activities[0]["place"])
            return JsonResponse({"new_activity": filtered_activities})
        if available_activities:
            return JsonResponse({"new_activity": available_activities})
        return JsonResponse({"message": "No new activities available"})

    return JsonResponse({"error": "Invalid request"}, status=400)

def remove_duplicate_activities(activities):
    unique_activities = []
    seen_places = set()

    for activity in activities:
        place = activity["place"]
        if place not in seen_places:
            seen_places.add(place)
            unique_activities.append(activity)

    return unique_activities

def get_activity_suggestions(weather, time_of_day, location, user_feedback=None):
    prompt = f"""
    You are an assistant that provides structured activity suggestions. 
    Based on the local weather ({weather}) and time of day ({time_of_day}), 
    suggest exactly 10 varied activities in {location}. 

    Ensure a **mix of indoor and outdoor activities**, regardless of the weather. 
    The activities should include a variety of options such as:  
    - Solo and group activities  
    - Relaxing and adventurous activities  
    - Family-friendly and social activities  

    Return the response **strictly** in JSON format as a list of objects.  
    Each object must have:
    - "place": A specific location where the activity can be done (e.g., "Central Park" or "City Mall").
    - "activity": A full sentence describing the activity (e.g., "Go for a relaxing jog at Central Park").

    **Output ONLY valid JSON** with no extra text, explanation, or formatting.
    """
    if user_feedback:
        prompt += f"  show result based on User Feedback: {user_feedback} to improve the suggestion and excluding the past suggestions {seen_places}."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        response_text = response['choices'][0]['message']['content'].strip()
                
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

def store_suggested_activities(request, activities):
    """Stores suggested activities in the user's session to avoid repetition."""
    if "seen_activities" not in request.session:
        request.session["seen_activities"] = []


    seen_places = request.session["seen_activities"]

    # Add new activities to session
    for activity in activities:
        if activity["place"] not in seen_places:
            seen_places.append(activity["place"])
    request.session["seen_activities"] = seen_places
    return activities

# Function to parse the opening hours into a structured dictionary
def parse_opening_hours(hours_list):
    parsed_hours = {}
    for entry in hours_list:
        match = re.match(r"(\w+): (\d{1,2}:\d{2})\s*(AM|PM) – (\d{1,2}:\d{2})\s*(AM|PM)", entry)
        if match:
            day, start, start_period, end, end_period = match.groups()
            start_time = datetime.strptime(f"{start} {start_period}", "%I:%M %p").strftime("%H:%M")
            end_time = datetime.strptime(f"{end} {end_period}", "%I:%M %p").strftime("%H:%M")
            parsed_hours[day] = (start_time, end_time)
    return parsed_hours

def is_place_open(parsed_hours):
    current_day = datetime.now().strftime("%A")  # Get current day (e.g., "Monday")
    current_time = datetime.now().strftime("%H:%M")  # Get current time (24-hour format)

    if current_day in parsed_hours:
        open_time, close_time = parsed_hours[current_day]
        return open_time <= current_time <= close_time  # Check if current time is within the range
    return False

def get_place_opening_hours(place_name):
    url = f'https://maps.googleapis.com/maps/api/place/textsearch/json?query={place_name}&key={GOOGLE_MAPS_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and len(data['results']) > 0:
            place_id = data['results'][0]['place_id']
        else:
            place_id = None
            return None
    else:
        print("Error fetching place details:", response.status_code)
        return None
    # Google Places API endpoint for place details
    url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=opening_hours&key={GOOGLE_MAPS_API_KEY}'
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if 'result' in data and 'opening_hours' in data['result']:
            opening_hours = data['result']['opening_hours']['weekday_text']
            opening_hours = parse_opening_hours(opening_hours)
            return opening_hours
        else:
            print("Opening hours not available for this place:", place_name)
            return None
    else:
        print("Error fetching place details:", response.status_code)
        return None
    
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

            if response.status_code == 200:
                weather_data = response.json()
                weather = {
                    'city': weather_data.get('name', 'Unknown'),
                    'temperature': weather_data['main']['temp'],
                    'description': weather_data['weather'][0]['description'],                }
                google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
                now = datetime.now().hour
                if 6 <= now < 12:
                    time_of_day = "morning"
                elif 12 <= now < 18:
                    time_of_day = "afternoon"
                elif 18 <= now < 23:
                    time_of_day = "evening"
                else:
                    time_of_day = "night"
                # Store weather, time_of_day, and city in session
                request.session["weather_description"] = weather['description']
                request.session["time_of_day"] = time_of_day
                request.session["city"] = weather['city']
                activities = get_activity_suggestions(weather['description'], time_of_day, weather['city'])
                # Filter activities that are open
                available_activities = []
                for activity in activities:
                    place_name = activity['place']
                    opening_hours = get_place_opening_hours(place_name)
                    if opening_hours and is_place_open(opening_hours):
                        available_activities.append(activity)
                available_activities = remove_duplicate_activities(available_activities)
                available_activities = store_suggested_activities(request, remove_duplicate_activities(available_activities))
                response_data = ({
                    "status": "success", 
                    "weather": weather,
                    "activities": available_activities
                    })
                return JsonResponse(response_data)
            else:
                return JsonResponse({"status": "error", "message": "Could not fetch weather"}, status=500)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

