#!/usr/bin/env python3

import requests
import os
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

def register():
    email = input("Email: ").strip()
    
    if not email or "@" not in email:
        print("Invalid email address")
        return
    
    response = requests.post(
        f"{API_URL}/register",
        json={"email": email},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        try:
            data = response.json()
            if data.get("status") == "pending_verification":
                print("Code already sent. Check your email.")
            else:
                print("Verification code sent to your email. Check spam folder if not in Inbox.")
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Response: {response.text}")
            return
    else:
        try:
            print(response.json()['detail'])
        except Exception:
            print(f"Error {response.status_code}: {response.text}")
        return
    
    code = input("Enter code: ").strip()
    
    response = requests.post(
        f"{API_URL}/verify",
        json={"email": email, "code": code},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        try:
            api_key = response.json()["api_key"]
            print(f"\nAPI Key: {api_key}")
            save_api_key(api_key, email)
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Response: {response.text}")
    else:
        try:
            print(response.json()['detail'])
        except Exception:
            print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    register()

