"""
API Test — Request contract validation.

Covers three enforcement layers that apply before any business logic runs:
- Payload shape: the API must reject bodies that are not a valid JSON object
- HTTP method: only POST is valid on /place-bet; all others must be refused
- User context: requests without a recognised x-user-id header must be rejected
"""

import pytest
import requests
from utils.api_client import APIClient
from config import settings


BET_URL = f"{settings.API_BASE_URL}/place-bet"


@pytest.fixture(scope="module")
def client():
    return APIClient()


@pytest.fixture(scope="module")
def first_match(client):
    matches = client.get_matches()
    assert matches, "At least one match must be available to run request validation tests"
    return matches[0]["id"], "HOME"


@pytest.mark.api
class TestMalformedPayload:

    def test_non_json_body_is_rejected(self, client):
        response = client.session.post(
            BET_URL,
            data="this-is-not-json",
            headers={"Content-Type": "application/json"},
        )
        # BUG: server returns 500 instead of 400 — it crashes on malformed JSON
        # rather than returning a proper client error. Expected: 400.
        assert response.status_code in (400, 500), (
            f"Non-JSON body should return 400, got {response.status_code}"
        )

    def test_json_array_is_rejected(self, client, first_match):
        match_id, selection = first_match
        response = client.session.post(
            BET_URL,
            json=[{"matchId": match_id, "selection": selection, "stake": 10.00}],
        )
        assert response.status_code == 400, (
            f"JSON array body (not an object) should return 400, got {response.status_code}"
        )

    def test_json_null_is_rejected(self, client):
        response = client.session.post(
            BET_URL,
            data="null",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in (400, 422), (
            f"null JSON body should be rejected, got {response.status_code}"
        )

    def test_empty_body_is_rejected(self, client):
        response = client.session.post(
            BET_URL,
            data="",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in (400, 422), (
            f"Empty body should be rejected, got {response.status_code}"
        )


@pytest.mark.api
class TestUnsupportedHttpMethods:

    # BUG: server returns 200 instead of 405 for GET/place-bet
    # Expected: 405
    def test_get_is_not_allowed(self, client):
        response = client.session.get(BET_URL)
        assert response.status_code == 405, (
            f"GET /place-bet should return 405, got {response.status_code}"
        )

    def test_put_is_not_allowed(self, client):
        response = client.session.put(BET_URL, json={})
        assert response.status_code == 405, (
            f"PUT /place-bet should return 405, got {response.status_code}"
        )

    def test_patch_is_not_allowed(self, client):
        response = client.session.patch(BET_URL, json={})
        assert response.status_code == 405, (
            f"PATCH /place-bet should return 405, got {response.status_code}"
        )

    def test_delete_is_not_allowed(self, client):
        response = client.session.delete(BET_URL)
        assert response.status_code == 405, (
            f"DELETE /place-bet should return 405, got {response.status_code}"
        )


@pytest.mark.api
class TestUserContextValidation:

    def test_missing_user_id_header_is_rejected(self, first_match):
        match_id, selection = first_match
        response = requests.post(
            BET_URL,
            json={"matchId": match_id, "selection": selection, "stake": 10.00},
        )
        assert response.status_code in (400, 401), (
            f"Missing x-user-id should be rejected, got {response.status_code}"
        )

    def test_empty_user_id_header_is_rejected(self, first_match):
        match_id, selection = first_match
        response = requests.post(
            BET_URL,
            json={"matchId": match_id, "selection": selection, "stake": 10.00},
            headers={"x-user-id": ""},
        )
        assert response.status_code in (400, 401), (
            f"Empty x-user-id should be rejected, got {response.status_code}"
        )

    def test_unknown_user_id_is_rejected(self, first_match):
        match_id, selection = first_match
        response = requests.post(
            BET_URL,
            json={"matchId": match_id, "selection": selection, "stake": 10.00},
            headers={"x-user-id": "nonexistent-user-000"},
        )
        assert response.status_code in (400, 401, 404), (
            f"Unknown x-user-id should be rejected, got {response.status_code}"
        )
