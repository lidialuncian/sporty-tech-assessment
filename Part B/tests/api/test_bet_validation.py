"""
API Test — Stake boundary and balance validation rules (SBP-03, SBP-05).

Chosen because stake validation is the primary financial guard of the platform:
it enforces the minimum (€1.00), maximum (€100.00), and decimal precision (2dp)
rules defined in the spec, and prevents over-betting when the user has
insufficient funds. Testing these at the API layer — independently of the UI —
confirms that the business rules are enforced server-side and cannot be bypassed
by manipulating the frontend. The spec explicitly marks these rules as enforced
at both UI + API layer (section 4.1).
"""

import pytest
from utils.api_client import APIClient


@pytest.fixture(scope="module")
def client():
    return APIClient()


@pytest.fixture(scope="module")
def first_match(client):
    """Returns (match_id, selection) for the first match returned by the API."""
    matches = client.get_matches()
    assert matches, "At least one match must be available to run bet validation tests"
    return matches[0]["id"], "HOME"


@pytest.fixture(autouse=True)
def reset_balance_before_each(client):
    """Resets balance to the initial value before every test for isolation."""
    client.reset_balance()


@pytest.mark.api
class TestStakeBoundaryValidation:

    def test_stake_below_minimum_is_rejected(self, client, first_match):
        match_id, selection = first_match
        response = client.place_bet(match_id, selection, stake=0.99)

        assert response.status_code == 422, (
            f"Stake 0.99 (below minimum €1.00) should return 422, got {response.status_code}"
        )

    def test_stake_at_minimum_is_accepted(self, client, first_match):
        match_id, selection = first_match
        response = client.place_bet(match_id, selection, stake=1.00)

        assert response.status_code == 200, (
            f"Stake €1.00 (minimum boundary) should be accepted with 200, got {response.status_code}"
        )
        body = response.json()
        assert body["stake"] == 1.00
        assert body["balance"] is not None

    def test_stake_at_maximum_is_accepted(self, client, first_match):
        match_id, selection = first_match
        response = client.place_bet(match_id, selection, stake=100.00)

        assert response.status_code == 200, (
            f"Stake €100.00 (maximum boundary) should be accepted with 200, got {response.status_code}"
        )
        body = response.json()
        assert body["stake"] == 100.00

    def test_stake_above_maximum_is_rejected(self, client, first_match):
        match_id, selection = first_match
        response = client.place_bet(match_id, selection, stake=100.01)

        assert response.status_code == 422, (
            f"Stake €100.01 (above maximum) should return 422, got {response.status_code}"
        )

    def test_stake_with_three_decimal_places_is_rejected(self, client, first_match):
        match_id, selection = first_match
        response = client.place_bet(match_id, selection, stake=10.001)

        assert response.status_code == 422, (
            f"Stake 10.001 (3 decimal places) should return 422, got {response.status_code}"
        )

    def test_missing_stake_is_rejected(self, client, first_match):
        match_id, selection = first_match
        response = client.place_bet(match_id, selection, stake=None)

        assert response.status_code in (400, 422), (
            f"Missing stake should be rejected, got {response.status_code}"
        )


@pytest.mark.api
class TestInsufficientBalanceValidation:

    def test_stake_exceeding_balance_is_rejected(self, client, first_match):
        """
        Confirms the API enforces the 'stake must not exceed available balance' rule
        and that the balance is unchanged after a rejected bet.
        """
        match_id, selection = first_match

        balance_before = client.get_balance()["balance"]

        # Drain the balance close to zero with a valid bet, then try to over-bet
        drain_stake = min(round(balance_before - 0.50, 2), 100.00)
        drain_response = client.place_bet(match_id, selection, stake=drain_stake)
        assert drain_response.status_code == 200, "Setup drain bet should succeed"

        remaining = client.get_balance()["balance"]
        over_stake = min(round(remaining + 1.00, 2), 100.00)

        if over_stake <= remaining:
            pytest.skip("Cannot produce an insufficient balance scenario within stake limits")

        response = client.place_bet(match_id, selection, stake=over_stake)

        assert response.status_code == 422, (
            f"Stake exceeding balance should return 422, got {response.status_code}"
        )

        # Balance must be unchanged after the rejected bet
        balance_after = client.get_balance()["balance"]
        assert balance_after == remaining, (
            f"Balance must not change after rejected bet: expected {remaining}, got {balance_after}"
        )


@pytest.mark.api
class TestSelectionValidation:

    def test_invalid_selection_value_is_rejected(self, client, first_match):
        """API must reject selection values outside HOME / DRAW / AWAY"""
        match_id, _ = first_match
        response = client.place_bet(match_id, "WIN", stake=10.00)

        assert response.status_code == 422, (
            f"Invalid selection 'WIN' should return 422, got {response.status_code}"
        )

    def test_missing_selection_is_rejected(self, client, first_match):
        match_id, _ = first_match
        response = client.place_bet(match_id, None, stake=10.00)

        assert response.status_code in (400, 422), (
            f"Missing selection should be rejected, got {response.status_code}"
        )

    def test_unknown_match_id_is_rejected(self, client):
        response = client.place_bet("nonexistent-match-id", "HOME", stake=10.00)

        assert response.status_code == 422, (
            f"Unknown matchId should return 422, got {response.status_code}"
        )
        assert response.json()["message"]  == "Match not found."
