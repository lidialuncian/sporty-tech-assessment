# Part B — Automation Project

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| UI automation | Selenium WebDriver 4 + Pytest |
| API testing | Python `requests` |
| Browser | Latest desktop Chrome (managed automatically via `webdriver-manager`) |
| Reporting | pytest-html |

---

## Project Structure

```
Part B/
├── config/
│   └── settings.py               # Central config — reads from .env
├── pages/                        # Page Object Model
│   ├── base_page.py              # Shared Selenium helpers (waits, click, type)
│   └── place_single_bet_page.py  # Full page — match list, bet slip, receipt modal
├── tests/
│   ├── e2e/
│   │   └── test_bet_placement.py      # UI: successful bet placement journey
│   └── api/
│       ├── test_bet_validation.py     # API: stake rules, balance, selection validation
│       └── test_request_validation.py # API: malformed payloads, HTTP methods, user context
├── utils/
│   └── api_client.py             # requests wrapper (x-user-id auth, all endpoints)
├── conftest.py                   # Pytest fixtures (Chrome driver, page object factory)
├── pytest.ini                    # Test discovery + default CLI options
├── requirements.txt              # Python dependencies (see explanation below)
├── .env.example
└── .env                          # Local only — not committed
```

---

## Dependencies — `requirements.txt`

| Package | Version | Purpose |
|---|---|---|
| `selenium` | 4.27.1 | Browser automation — drives Chrome to interact with the UI just like a real user |
| `pytest` | 8.3.4 | Test runner — discovers, executes, and reports on all tests in the `tests/` directory |
| `pytest-html` | 4.1.1 | Generates `reports/report.html` after each run with a visual summary of results and failure logs |
| `webdriver-manager` | 4.0.2 | Automatically downloads the correct ChromeDriver version to match the installed Chrome — no manual setup needed |
| `requests` | 2.32.3 | HTTP client used for all API tests — sends REST calls directly to the backend, bypassing the UI |
| `python-dotenv` | 1.0.1 | Loads `BASE_URL`, `API_BASE_URL`, and `USER_ID` from the `.env` file into `settings.py` at runtime |

---

## Setup

### 1. Prerequisites

- Python 3.11+
- Google Chrome (latest)

### 2. Install dependencies

```bash
cd "Part B"
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> ChromeDriver is managed automatically by `webdriver-manager` — no manual download needed.

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set your user ID:

```
BASE_URL=https://qae-assignment-tau.vercel.app
API_BASE_URL=https://qae-assignment-tau.vercel.app/api
USER_ID=your-user-id-here
```

**Authentication model:** the app uses `?user-id=<id>` as a URL query parameter for the UI, and an `x-user-id: <id>` header for all API calls. There is no login form.

---

## Running the tests

### Run all tests

```bash
pytest
```

### Run only E2E UI tests

```bash
pytest -m e2e
```

### Run only API tests

```bash
pytest -m api
```

### Run a specific test file

```bash
pytest tests/e2e/test_bet_placement.py
pytest tests/api/test_bet_validation.py
pytest tests/api/test_request_validation.py
```

### Run in headless mode (CI / no display)

Pass the `--headless` flag or set the env var before running:

```bash
HEADLESS=true pytest
```

> To enable headless, uncomment `options.add_argument("--headless=new")` in `conftest.py`.

---

## HTML report

An HTML report is generated automatically after each run:

```
reports/report.html
```

---

## Tests at a glance

### E2E — `tests/e2e/test_bet_placement.py`

**`test_successful_single_bet_placement`** (covers SBP-01)

Full happy-path journey: open app → select odds → enter stake → verify potential payout calculation → place bet → assert loading state → assert all receipt fields are populated → close receipt → assert no active selection remains → assert balance was deducted. The balance assertion specifically catches the critical regression SBP-08 (balance not deducted after placement).

---

### API — `tests/api/test_bet_validation.py`

**`TestStakeBoundaryValidation`** (covers SBP-05)

Six cases covering all stake rules enforced at the API layer: minimum boundary (€1.00), maximum boundary (€100.00), above-max, below-min, 3-decimal-place precision, and missing stake. All expect HTTP 422 on failure and 200 on acceptance.

**`TestInsufficientBalanceValidation`** (covers SBP-03)

Drains the balance to near zero, then attempts an over-stake. Expects 422 and confirms balance is unchanged after rejection.

**`TestSelectionValidation`** (covers spec 4.2)

Confirms the API rejects invalid selection values, missing selection, and unknown match IDs.

---

### API — `tests/api/test_request_validation.py`

**`TestMalformedPayload`**

Four cases verifying the API rejects request bodies that are not a valid JSON object: a plain string, a JSON array, a JSON `null`, and an empty body. All expect 400 or 422 before any business logic is reached.

**`TestUnsupportedHttpMethods`**

Confirms that GET, PUT, PATCH, and DELETE are all refused on `/place-bet` with HTTP 405 Method Not Allowed — only POST is a valid method for this endpoint.

**`TestUserContextValidation`**

Three cases covering the `x-user-id` header enforcement: missing header, empty string, and an unknown user ID. All expect 400 or 401. These tests bypass `APIClient` and use raw `requests` calls so no header is injected by the session.

---

## Design decisions

- **Page Object Model** — all UI interactions are in `pages/`; locator changes are a one-file fix.
- **`button.oddsButton[id^='odds-']` selector** — scopes to the button tag and the `oddsButton` CSS class, preventing accidental matches on non-interactive elements (e.g. the filter toggle) that share the `odds-` ID prefix.
- **`find_clickable` before clicking odds** — waits for the button to be interactable, not just present in the DOM, avoiding races on page load.
- **`BasePage` centralises waits** — no duplicated `WebDriverWait` calls across page objects.
- **`APIClient` with `requests.Session`** — the `x-user-id` header is set once on the session and sent on every request automatically.
- **`reset_balance` fixture** — each test resets balance via `POST /api/reset-balance` so tests are order-independent and repeatable.
- **`scope="module"` for match lookup** — the match list is fetched once per module; balance reset runs per-test via `autouse`.
