from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from config import settings


class PlaceSingleBetPage(BasePage):

    # --- Header ---
    BALANCE_DISPLAY = (By.ID, "header-balance")

    # --- Match list ---
    MATCH_LIST = (By.ID, "match-section")
    MATCH_ITEMS = (By.CSS_SELECTOR, "[id^='match-card-']")
    ODDS_BUTTON = (By.CSS_SELECTOR, "button.oddsButton[id^='odds-']")

    # --- Bet slip ---
    # div#bet-slip qualified with tag — the Remove All button shares the same id (app bug)
    BET_SLIP = (By.CSS_SELECTOR, "div#bet-slip")
    SELECTION_CARD = (By.CSS_SELECTOR, ".betSelectionCard")
    REMOVE_SELECTION = (By.ID, "bet-slip-selection-remove")
    REMOVE_ALL = (By.CSS_SELECTOR, "button#bet-slip")
    SELECTED_ODDS = (By.CSS_SELECTOR, ".betSelectionOdds")

    # --- Stake ---
    STAKE_INPUT = (By.ID, "bet-slip-stake-input")
    TOTAL_STAKE = (By.ID, "bet-slip-total-stake")
    POTENTIAL_PAYOUT = (By.ID, "bet-slip-potential-payout")

    # --- Place Bet button ---
    PLACE_BET_BUTTON = (By.ID, "bet-slip-place-bet")
    # Button retains [disabled] while the request is in flight ("Placing...")
    PLACING_INDICATOR = (By.CSS_SELECTOR, ".placeBetButtonPlacing")

    # --- Validation error ---
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".betSlipError")

    # --- Receipt modal ---
    RECEIPT_MODAL = (By.ID, "modal-success")
    RECEIPT_BET_ID = (By.ID, "modal-success-bet-id")
    RECEIPT_MATCH_DETAILS = (By.ID, "modal-success-match")
    RECEIPT_STAKE = (By.ID, "modal-success-stake")
    RECEIPT_ODDS = (By.ID, "modal-success-odds")
    RECEIPT_PAYOUT = (By.ID, "modal-success-payout")
    RECEIPT_TIMESTAMP = (By.ID, "modal-success-placed-at")
    RECEIPT_CLOSE_BUTTON = (By.ID, "modal-success-close")

    # Page / match list
    def open(self):
        self.driver.get(f"{settings.BASE_URL}?user-id={settings.USER_ID}")
        self.find(self.MATCH_LIST)

    def get_balance(self):
        raw = self.get_text(self.BALANCE_DISPLAY)
        # Text format: keep only digits and decimal point
        return float("".join(c for c in raw if c.isdigit() or c == "."))

    def select_first_available_odds(self):
        self.find_all(self.ODDS_BUTTON)
        self.find_clickable(self.ODDS_BUTTON).click()

    # Bet slip
    def has_selection(self):
        return self.is_visible(self.SELECTION_CARD)

    def enter_stake(self, amount):
        self.type_text(self.STAKE_INPUT, str(amount))

    def click_place_bet(self):
        self.click(self.PLACE_BET_BUTTON)

    def wait_for_placing_state(self):
        self.find(self.PLACING_INDICATOR)
        
    def get_total_stake(self):
        raw = self.get_text(self.TOTAL_STAKE)
        return float("".join(c for c in raw if c.isdigit() or c == "."))

    def get_selected_odds(self):
        raw = self.get_text(self.SELECTED_ODDS)
        return float("".join(c for c in raw if c.isdigit() or c == "."))

    def verify_potential_payout(self):
        stake = self.get_total_stake()
        odds = self.get_selected_odds()
        raw = self.get_text(self.POTENTIAL_PAYOUT)
        displayed_payout = float("".join(c for c in raw if c.isdigit() or c == "."))
        return displayed_payout == round(stake * odds, 2)


    # Receipt modal
    def wait_for_receipt(self):
        return self.find_visible(self.RECEIPT_MODAL)

    def get_receipt_details(self):
        return {
            "bet_id": self.get_text(self.RECEIPT_BET_ID),
            "match_details": self.get_text(self.RECEIPT_MATCH_DETAILS),
            "stake": self.get_text(self.RECEIPT_STAKE),
            "odds": self.get_text(self.RECEIPT_ODDS),
            "payout": self.get_text(self.RECEIPT_PAYOUT),
            "timestamp": self.get_text(self.RECEIPT_TIMESTAMP),
        }

    def close_receipt(self):
        self.click(self.RECEIPT_CLOSE_BUTTON)
        self.wait_for_invisible(self.RECEIPT_MODAL)

    # Error state
    def get_error_message(self):
        return self.get_text(self.ERROR_MESSAGE)

    def has_error(self):
        return self.is_visible(self.ERROR_MESSAGE)
