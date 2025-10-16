#!/usr/bin/env python3

import requests
from pathlib import Path

API_URL = "https://sparq-api.onrender.com"

def save_api_key(api_key, email):
    config_dir = Path.home() / ".sparq"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.txt"
    
    with open(config_file, "w") as f:
        f.write(f"API_KEY={api_key}\n")
        f.write(f"EMAIL={email}\n")
    
    print(f"\nAPI key saved to {config_file}")

def recover_key():
    email = input("Email: ").strip()
    
    if not email or "@" not in email:
        print("Invalid email address")
        return
    
    try:
        response = requests.post(
            f"{API_URL}/recover",
            json={"email": email},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")
            return
        
        print("Verification code sent to your email. Check spam folder if not in Inbox.")
    except Exception as e:
        print(f"Error connecting to API: {e}")
        return
    
    code = input("Enter code: ").strip()
    
    try:
        response = requests.post(
            f"{API_URL}/recover",
            json={"email": email, "code": code},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            api_key = response.json()["api_key"]
            print(f"\nAPI Key: {api_key}")
            save_api_key(api_key, email)
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        print(f"Error connecting to API: {e}")

if __name__ == "__main__":
    recover_key()
