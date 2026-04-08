import requests
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.urls import reverse
from django.conf import settings

def refresh_soundcloud_token(social):
    CLIENT_ID = settings.SOCIAL_AUTH_SOUNDCLOUD_KEY
    CLIENT_SECRET = settings.SOCIAL_AUTH_SOUNDCLOUD_SECRET
    
    refresh_token = social.extra_data.get('refresh_token')
    
    if not refresh_token:
        print("Refresh token відсутній!")
        return False
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Ключі CLIENT_ID або CLIENT_SECRET SoundCloud відсутні в settings.")
        return False

    token_url = "https://api.soundcloud.com/oauth2/token"
    data = {
        'client_id': CLIENT_ID,                  
        'client_secret': CLIENT_SECRET,         
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }
    
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        new_token_data = response.json()
        
        social.extra_data['access_token'] = new_token_data.get('access_token')
        if 'refresh_token' in new_token_data:
            social.extra_data['refresh_token'] = new_token_data.get('refresh_token')
        social.save()
        
        print("Токен SoundCloud успішно оновлено!")
        return True
    
    except requests.RequestException as e:
        print(f"Помилка оновлення токена SoundCloud: {e}")
        return False


def home(request):
    user = request.user
    access_token = None
    social = None

    if user.is_authenticated:
        social = user.social_auth.filter(provider='soundcloud').first()
        if social:
            access_token = social.extra_data.get('access_token')

    tracks = []
    error = None
    query = None

    if not access_token:
        error = "Відсутній access token, будь ласка, увійдіть через SoundCloud."
    else:
        query = request.GET.get('q')
        if query:
            url = "https://api.soundcloud.com/tracks"
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            params = {
                "q": query,
                "limit": 10,
                "filter": "public",
            }
            
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 401:
                print("Отримано 401. Спроба оновити токен...")
                if social and refresh_soundcloud_token(social):
                    new_access_token = social.extra_data.get('access_token')
                    if new_access_token:
                        headers["Authorization"] = f"Bearer {new_access_token}"
                        response = requests.get(url, headers=headers, params=params)
                    else:
                        error = "Токен оновлено, але новий access_token відсутній."
                else:
                    error = "Термін дії access token минув, і його не вдалося оновити. Спробуйте увійти знову."
            
            
            if response.status_code == 200:
                try:
                    tracks = response.json()
                except Exception as e:
                    error = f"JSON decode error: {e}"
            elif response.status_code != 401:
                error = f"SoundCloud API error: {response.status_code} - {response.text}"

    return render(request, "home.html", {
        "tracks": tracks, 
        "query": query, 
        "error": error
    })

def logout_view(request):
    if request.user.is_authenticated:
        social = request.user.social_auth.filter(provider='soundcloud').first()
        if social:
            social.delete()
            print("Соціальний запис SoundCloud видалено.")
        logout(request)
        
    return redirect(reverse('home'))