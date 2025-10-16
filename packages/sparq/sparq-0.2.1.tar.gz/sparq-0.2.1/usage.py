import requests
from pathlib import Path

API_URL = "https://sparq-api.onrender.com"

def load_api_key():
    config_path = Path.home() / ".sparq" / "config.txt"
    if not config_path.exists():
        return None
    with open(config_path, "r") as f:
        for line in f:
            if line.startswith("API_KEY="):
                return line.strip().split("=", 1)[1]
    return None

def show_usage(api_key=None):
    if not api_key:
        api_key = load_api_key()
        if not api_key:
            print("No API key found. Please run auth.py to register first.")
            return
    
    try:
        response = requests.get(
            f"{API_URL}/usage",
            headers={"x-api-key": api_key}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\nEmail: {data['email']}")
            print(f"Total API Calls: {data['total_api_calls']}\n")
            
            if data['recent_calls']:
                print("Recent Calls:")
                for i, call in enumerate(data['recent_calls'], 1):
                    major = call.get('request_data', {}).get('major', 'N/A') if call.get('request_data') else 'N/A'
                    print(f"  {i}. {call['endpoint']} | {call['response_status']} | {major} | {call['created_at']}")
            else:
                print("No API calls recorded yet.\n")
        
        elif response.status_code == 401:
            print("Invalid or inactive API key")
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")
    
    except requests.exceptions.ConnectionError:
        print(f"Cannot connect to API at {API_URL}")
        print("Make sure the server is running")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    show_usage()
