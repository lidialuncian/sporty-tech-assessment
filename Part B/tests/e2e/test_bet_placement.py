"""
E2E UI Test — SBP-01: Successful single bet placement (critical user journey).

Chosen because this is the core revenue-generating flow of the platform.
If a valid bet cannot be placed end-to-end — selection → stake → confirm →
receipt — the product fails its primary purpose. It also exercises the full
UI stack: match list interaction, bet slip state management, loading feedback,
and the success receipt modal, giving broad regression coverage in one test.
The balance deduction assertion additionally catches the critical bug class
where placement succeeds visually but financial state is not updated (SBP-08).
"""

import pytest
from utils.api_client import APIClient


VALID_STAKE = 10.00


@pytest.fixture(autouse=True)
def reset_balance():
    """Resets the balance via API before the test so the starting state is predictable."""
    APIClient().reset_balance()


@pytest.mark.e2e
class TestBetPlacement:

    def test_successful_single_bet_placement(self, app):
        page = app

        balance_before = page.get_balance()

        # Select the first available odds from the match list
        page.select_first_available_odds()

        # Verify exactly one selection appeared in the bet slip
        assert page.has_selection(), "Bet slip should show an active selection after clicking odds"

        # Enter a valid stake and submit
        page.enter_stake(VALID_STAKE)
        assert page.verify_potential_payout(), "Potential payout was calculated correctly"

        # Place bet
        page.click_place_bet()

        # Button must enter loading / disabled state immediately on submit
        page.wait_for_placing_state()

        # Wait for the success receipt modal to appear
        page.wait_for_receipt()
        receipt = page.get_receipt_details()

        # All required receipt fields must be populated
        assert receipt["bet_id"], "Receipt must include a bet ID"
        assert receipt["match_details"], "Receipt must include the match details"
        assert receipt["stake"], "Receipt must display the stake"
        assert receipt["odds"], "Receipt must display the odds at placement"
        assert receipt["payout"], "Receipt must display the potential payout"
        assert receipt["timestamp"], "Receipt must include a placement timestamp"

        # Close receipt — user must be returned to a clean state with no active selection
        page.close_receipt()
        assert not page.has_selection(), "Bet slip should be empty after closing the receipt"

        # Balance must be reduced by exactly the staked amount
        balance_after = page.get_balance()
        expected_balance = round(balance_before - VALID_STAKE, 2)
        assert balance_after == expected_balance, (
            f"Expected balance {expected_balance} after €{VALID_STAKE} stake, got {balance_after}"
        )
