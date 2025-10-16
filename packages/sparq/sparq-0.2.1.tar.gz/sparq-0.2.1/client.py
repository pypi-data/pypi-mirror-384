#!/usr/bin/env python3

import requests
from pathlib import Path

API_URL = "https://sparq-api.onrender.com"

class Sparq:
    def __init__(self, api_key=None):
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = self._load_api_key()
    
    def _load_api_key(self):
        config_file = Path.home() / ".sparq" / "config.txt"
        if config_file.exists():
            with open(config_file, "r") as f:
                for line in f:
                    if line.startswith("API_KEY="):
                        return line.strip().split("=", 1)[1]
        return None
    
    def plan(self, major, cc_courses=None, ap_exams=None, sjsu_courses=None, units_per_semester=15):
        if not self.api_key:
            raise Exception("No API key found. Run auth.py first.")
        
        payload = {
            "major": major,
            "cc_courses": cc_courses or [],
            "ap_exams": ap_exams or [],
            "sjsu_courses": sjsu_courses or [],
            "units_per_semester": units_per_semester
        }
        
        response = requests.post(
            f"{API_URL}/plan",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.json().get('detail', 'Unknown error')}")
    
    def usage(self):
        """Get API usage statistics for the authenticated user."""
        if not self.api_key:
            raise Exception("No API key found. Run auth.py first.")
        
        response = requests.get(
            f"{API_URL}/usage",
            params={"x_api_key": self.api_key}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.json().get('detail', 'Unknown error')}")
    
    def events(self):
        """Get SJSU events from the events calendar."""
        if not self.api_key:
            raise Exception("No API key found. Run auth.py first.")
        
        response = requests.get(
            f"{API_URL}/events",
            headers={"x-api-key": self.api_key},
            timeout=45  # Events scraping can take a while
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.json().get('detail', 'Unknown error')}")
