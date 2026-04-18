# Part C — Test Strategy Justifications

## Why these two tests were selected for automation

The E2E test (`test_successful_single_bet_placement`) covers the core revenue-generating flow of the platform. If a user cannot select odds, enter a stake, and receive a receipt, the product fails its primary purpose — so this is the first flow that must never regress. That said, the current implementation only validates the main happy path. Several assertions are still missing: the payout calculation displayed before submission, match details on the receipt, and the odds value persisted at placement time. These gaps mean the test gives confidence the flow completes, but not that all data shown to the user is correct.

The API validation suite (`test_bet_validation.py`, `test_request_validation.py`) was prioritised because the business rules it covers — stake boundaries, balance enforcement, selection validity, and request contract — are enforced server-side and must hold regardless of what the UI does. Testing these at the API layer is faster, more stable, and catches bypass attempts that E2E tests cannot.

---

## What was left as manual only and why

The goal should be to automate as much as possible. The only category that genuinely cannot be fully automated is performance testing — load, stress, and latency testing require dedicated tooling and infrastructure that is outside the scope of a Selenium + pytest setup. These should still be part of the process, run against staging on a schedule or before major releases, but they live in a separate pipeline.

Everything else is a candidate for automation given time and tooling:

- **Receipt modal appearance and layout** — currently manual because visual regression requires a tool like Percy or Playwright's screenshot diffing. The functional assertions (fields populated, modal closes) are already automated; visual checks are the only remaining manual piece.
- **Cross-browser and responsive behaviour** — manual today because the setup is Chrome-only. Automatable via Selenium Grid or BrowserStack once a browser matrix is defined. Should be added to CI as a scheduled nightly job rather than on every PR.
- **Negative UI paths (invalid stake, error messages)** — not yet automated but fully automatable with the existing Selenium setup. These should be the next tests written.
- **Odds filter behaviour** — automatable once stable `data-testid` attributes are added to the filter toggle and filtered match list. Currently blocked by selector ambiguity (the filter toggle shares the `odds-` ID prefix with odds buttons).


---

## Top recommendations if this project were to scale

**1. Integrate into CI/CD**
Run the API tests on every pull request and the E2E suite on every merge to main. The API tests are fast enough (~seconds) to block a PR. The E2E tests should run headless in a container. A failing E2E on main should block deployment. This turns the test suite from a local tool into an actual safety net.

**2. Expand automated coverage — negative UI paths, cross-browser, performance**
The current E2E test only walks the happy path. Automate the negative UI path next (invalid stake → error message visible, place bet button disabled) and add missing assertions on payout value and receipt odds. Cross-browser coverage should be added as a scheduled nightly job. Performance testing (load, stress, latency) should run in a dedicated pipeline and be part of the release process.

**3. Clarify and lock the spec before adding more tests**
Several behaviours are currently ambiguous — what happens if odds change mid-selection, whether the receipt must show the odds at placement time vs current odds, and what constitutes a valid user ID. 
