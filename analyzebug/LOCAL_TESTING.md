# Local Testing Guide

This project now supports historical analysis in two ways:

1. standalone local analysis with a Python script
2. integrated UI/API support inside Gophish

## 0. Quick Demo With Included Synthetic Data

If you just want to validate the behavior without using your own campaign
export, use the bundled sample:

```bash
python3 analyzebug/campaign_truth.py \
  --input analyzebug/sample_campaign_results.json \
  --view compare
```

Expected current result:

- `dashboard.opened = 5`
- `actual.opened = 4`

The built-in gap is intentional in this fixture. `grace@example.test` has final
status `Email Opened`, but the matching timeline open event is missing. This
simulates the old silent event-write bug.

Historical snapshot before later interactions:

```bash
python3 analyzebug/campaign_truth.py \
  --input analyzebug/sample_campaign_results.json \
  --mode snapshot \
  --end 2026-01-12T12:00:00Z \
  --view compare
```

Expected snapshot highlights:

- `actual.opened = 2` from `bob` and `frank`
- `actual.clicked = 1` from `frank`
- `actual.submitted_data = 0`

Range example:

```bash
python3 analyzebug/campaign_truth.py \
  --input analyzebug/sample_campaign_results.json \
  --mode range \
  --start 2026-01-12T13:00:00Z \
  --end 2026-01-12T17:00:00Z \
  --view actual
```

Expected range highlights:

- `opened = 2` from `carol` and `dave`
- `clicked = 2` from `carol` and `dave`
- `submitted_data = 1` from `dave`

## 1. Standalone Python Script

Use this when you only have an exported campaign JSON and do not want to patch
or rebuild the platform.

### Input

Save the output of:

- `GET /api/campaigns/:id/results`

The file must contain:

- `results`
- `timeline`

### Commands

Compare current dashboard rollup vs event-derived historical truth:

```bash
python3 analyzebug/campaign_truth.py --input results.json --view compare
```

Snapshot at a cutoff timestamp:

```bash
python3 analyzebug/campaign_truth.py \
  --input results.json \
  --mode snapshot \
  --end 2026-01-12T10:30:00Z \
  --view compare
```

First reached inside a window:

```bash
python3 analyzebug/campaign_truth.py \
  --input results.json \
  --mode range \
  --start 2026-01-12T09:00:00Z \
  --end 2026-01-12T18:00:00Z \
  --view compare
```

JSON output:

```bash
python3 analyzebug/campaign_truth.py \
  --input results.json \
  --mode snapshot \
  --end 2026-01-12T10:30:00Z \
  --view compare \
  --output json
```

## 2. Backend / Test Validation

Run the full Go test suite:

```bash
go test ./...
```

Run only the directly relevant tests:

```bash
go test ./models -check.f 'TestGetCampaignRangeStatsSnapshot|TestGetCampaignRangeStatsRange|TestGetCampaignResultsOrdersEvents|TestHandleEmailOpenedDoesNotUpdateResultWhenEventSaveFails'
go test ./controllers/api -run TestCampaignRangeStats
```

## 3. Frontend Build

If you changed the source JS files, rebuild the minified assets:

```bash
npm install
npx gulp scripts
```

## 4. Manual UI Test

### Local Sample Page

If you want to inspect the browser UI without creating or launching a real
campaign, start Gophish locally and open:

- `/campaigns/dev/sample-results`

You can also use the `Open Sample Results` button on the Campaigns page.

The sample page:

- uses the bundled `sample_campaign_results.json`
- is read-only
- supports the new `Historical Analysis` controls
- does not send email or write campaign data to the database

1. Start Gophish locally with your usual workflow.
2. Open a campaign results page.
3. Verify the new `Historical Analysis` panel appears.
4. Leave `View = Current Dashboard`.
   Expected:
   - charts behave exactly like before
5. Change `View = Historical Events`.
6. Use `Snapshot At End` and set an end timestamp before a known later click or
   submit event.
   Expected:
   - charts reflect only the cumulative event state up to that cutoff
   - summary compares `Historical Events` vs `Current Dashboard`
7. Change to `First Reached In Range` and set start/end.
   Expected:
   - charts count the recipients whose first matching event happened inside the
     selected window
8. Open browser devtools and confirm requests go to:
   - `/api/campaigns/:id/range-stats?...`

## 5. Manual API Test

If you want to inspect the endpoint directly:

```bash
curl -H "Authorization: Bearer <API_KEY>" \
  "http://127.0.0.1:3333/api/campaigns/<ID>/range-stats?mode=snapshot&end=2026-01-12T10:30:00Z"
```

Range mode:

```bash
curl -H "Authorization: Bearer <API_KEY>" \
  "http://127.0.0.1:3333/api/campaigns/<ID>/range-stats?mode=range&start=2026-01-12T09:00:00Z&end=2026-01-12T18:00:00Z"
```

## Expected Semantics

### Dashboard

Derived from final `results.status`:

- `Submitted Data` implies clicked, opened, sent
- `Clicked Link` implies opened, sent
- `Email Opened` implies sent

### Historical Events

Derived from the earliest stored event per recipient:

- `snapshot`: stage reached on or before `end`
- `range`: stage first reached between `start` and `end`

## Important Limitation

For old campaigns affected by the silent event-write bug, missing event rows
cannot be reconstructed after the fact. The new fix prevents future drift, but
it cannot recreate data that was never stored.
