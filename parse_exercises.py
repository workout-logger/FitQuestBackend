import requests
import json

def get_tokens():
    url = 'https://wger.de/api/v2/token'
    credentials = {
        'username': 'loggerwork3@gmail.com',
        'password': 'wi4$%ji4v%4%$^2fhd5ivb'
    }
    response = requests.post(url, data=credentials)
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens['access']
        return access_token
    else:
        print("Failed to authenticate")
        return None

def verify_token(access_token):
    try:
        response = requests.post('https://wger.de/api/v2/token/verify', data={'token': access_token})
        response.raise_for_status()
        print("Token is valid")
    except requests.RequestException:
        print("Token is invalid or expired")

def get_exercises(access_token):
    url = 'https://wger.de/api/v2/exercisebaseinfo?limit=40000&offset=0'
    headers = {'Authorization': f'Bearer {access_token}'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        all_exercises = response.json()
        filtered_exercises = []
        for exercises in all_exercises['results']:
            for exercise in exercises['exercises']:
                # Filter for English language exercises with images
                if exercise['language'] == 2 and exercises['images'] and exercises['muscles']:
                    exercise_data = {
                        'name': exercise['name'],
                        'description': exercise['description'],
                        'muscles': [muscle['name_en'] for muscle in exercises['muscles'] if 'name_en' in muscle],
                        'images': [img['image'] for img in exercises['images']]
                    }
                    filtered_exercises.append(exercise_data)
        return filtered_exercises
    except requests.RequestException as e:
        print(f"Failed to fetch exercises: {e}")
        return None

def export_to_json(exercises):
    with open('exercises.json', 'w') as file:
        json.dump(exercises, file, indent=4)
        print("Data exported successfully to exercises.json")

def main():
    access_token = get_tokens()
    if access_token:
        verify_token(access_token)
        exercises = get_exercises(access_token)
        if exercises:
            print(exercises)  # Process or print exercises as needed
            export_to_json(exercises)

if __name__ == "__main__":
    main()
