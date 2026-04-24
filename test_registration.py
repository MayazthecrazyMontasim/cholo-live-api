import requests
import json

# Test the registration endpoint
url = "https://cholo-live-api-1.onrender.com/auth/register"
data = {
    "username": "testuser123",
    "email": "test123@example.com", 
    "password": "testpass123"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Text: {response.text}")
    
    if response.status_code == 200:
        print("SUCCESS: Registration endpoint is working!")
    else:
        print(f"ERROR: Got status code {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"Network Error: {e}")
