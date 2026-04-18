import requests
from config import settings


class APIClient:
    def __init__(self, user_id=None):
        self.base_url = settings.API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"x-user-id": user_id or settings.USER_ID})

    def get_matches(self):
        response = self.session.get(f"{self.base_url}/matches")
        response.raise_for_status()
        return response.json()

    def get_balance(self):
        response = self.session.get(f"{self.base_url}/balance")
        response.raise_for_status()
        return response.json()

    def place_bet(self, match_id, selection, stake):
        payload = {
            "matchId": match_id,
            "selection": selection,
            "stake": stake,
        }
        return self.session.post(f"{self.base_url}/place-bet", json=payload)

    def reset_balance(self):
        response = self.session.post(f"{self.base_url}/reset-balance")
        response.raise_for_status()
        return response.json()
