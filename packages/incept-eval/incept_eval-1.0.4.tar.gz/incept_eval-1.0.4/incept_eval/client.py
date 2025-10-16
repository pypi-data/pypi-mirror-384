"""HTTP client for Incept API"""
import requests

class InceptClient:
    def __init__(self, api_key, base_url="https://uae-poc.inceptapi.com", timeout=600):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })

    def evaluate_dict(self, data):
        url = f"{self.base_url}/v1/evaluate_unified"
        response = self.session.post(url, json=data, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
