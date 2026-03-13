# Gophish Campaign Metrics Analysis

This folder documents the campaign counting mismatch and provides a local tool
that can reproduce both views of the data without modifying the platform.

It also includes a synthetic saved results export:

- `sample_campaign_results.json`

That file is intentionally non-operational. It is only a local analysis fixture
for the Python tool and for manually validating the historical stats semantics.

## Verified Findings

1. The dashboard counts are a final-status rollup, not a raw event count.
   - `Clicked Link` implies `Email Opened`.
   - `Submitted Data` implies `Clicked Link` and `Email Opened`.
   - This matches the existing backend and frontend rollup logic.

2. A larger gap between dashboard counts and deduplicated events was caused by
   a real bug.
   - `models/result.go:createEvent` used to ignore `AddEvent(...)` errors.
   - If writing an event failed, `results.status` could still advance.
   - That made dashboard counts higher than the stored `timeline`.

3. Historical counts need two different semantics.
   - `snapshot`: cumulative state up to an end timestamp.
   - `range`: first time a recipient reached a stage inside a start/end window.

4. Existing historical data may already contain missing timeline rows.
   - The new fix prevents future silent drift.
   - Old campaigns cannot always be reconstructed perfectly if an event row was
     never stored.

## Added Platform Support

- New backend endpoint:
  - `GET /api/campaigns/:id/range-stats?mode=snapshot&end=<RFC3339>`
  - `GET /api/campaigns/:id/range-stats?mode=range&start=<RFC3339>&end=<RFC3339>`
- The endpoint returns:
  - `actual`: event-derived historical counts
  - `dashboard`: current final-status rollup
- The campaign results UI now has a small "Historical Analysis" control block
  with:
  - dashboard vs historical view
  - snapshot vs range mode
  - start/end pickers
  - apply/reset actions

## Local Script

`campaign_truth.py` reads a saved `/api/campaigns/:id/results` JSON response and
computes:

- current dashboard rollup
- historical event truth for `snapshot`
- historical event truth for `range`

Examples:

```bash
python3 analyzebug/campaign_truth.py --input results.json --view compare
python3 analyzebug/campaign_truth.py --input results.json --mode snapshot --end 2026-01-12T10:30:00Z --view actual
python3 analyzebug/campaign_truth.py --input results.json --mode range --start 2026-01-12T09:00:00Z --end 2026-01-12T18:00:00Z --view compare
```

## Tests Run

```bash
go test ./models -check.f 'TestGetCampaignRangeStatsSnapshot|TestGetCampaignRangeStatsRange|TestGetCampaignResultsOrdersEvents|TestHandleEmailOpenedDoesNotUpdateResultWhenEventSaveFails'
go test ./controllers/api -run TestCampaignRangeStats
```

Both commands passed in this environment after installing Go.
