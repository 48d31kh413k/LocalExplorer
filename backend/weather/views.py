from django.shortcuts import render
import requests
import os
from dotenv import load_dotenv
from django.http import JsonResponse


def get_weather(request):
    # url = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=imperial&appid='
    url = 'https://api.openweathermap.org/data/2.5/forecast?lat=57&lon=-2.15&appid='
    load_dotenv()
    api_key = os.getenv('WEATHER_API_KEY')
    url += api_key
    url += '&units=metric'

    #city = 'Casablanca'
    print(url)
    # city_weather = requests.get(url.format(city)).json() #request the API data and convert the JSON to Python data types
    city_weather = requests.get(url).json() #request the API data and convert the JSON to Python data types
    print(city_weather) #temporarily view output
    weather = {
        'city': city_weather['city']['name'],
        'temperature': city_weather['list'][0]['main']['temp'],
        'description': city_weather['list'][0]['weather'][0]['description'],
        'icon': city_weather['list'][0]['weather'][0]['icon']
    }
    
    return render(request, 'weather/index.html', {'weather': weather})