from OpenWeatherMap import get_weather
#import get_weather
#pip install requests[security]

def API_call():

# 
    api_key = get_weather.get_api_key()
#    print(api_key)
    
    location=get_weather.get_location()
#    print(location[0])

    weather = get_weather.get_weather(api_key, location[0],location[1],location[2])
# 
    #print(weather['main']['temp']-273.15,"°C",weather['main']['humidity'],"%")
   # print(weather)
    T=weather['main']['temp']-273.15
    RH=weather['main']['humidity']
    return T,RH

#API_T_RH=API_call()
#print(API_T_RH[0])
 
# if __name__ == '__main__':
#     main()