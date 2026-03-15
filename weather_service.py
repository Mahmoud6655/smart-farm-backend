def get_weather_data(city="Cairo"):
    api_key = "81c4a3e4f96d3fef12e316bbf5080160" 
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if response.status_code == 200:
            # سحب البيانات الحقيقية فوراً
            temp = data['main']['temp']
            humidity = data['main']['humidity']
            rain = data.get('rain', {}).get('1h', 0)
            return temp, humidity, rain
        else:
            # لو المدينة غلط أو الـ API فيه مشكلة، يرجع None عشان الـ Router يطلع Error للمستخدم
            print(f"Weather API Error: {data.get('message')}")
            return None, None, None
            
    except Exception as e:
        print(f"Connection Error: {e}")
        return None, None, None