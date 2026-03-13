# Pull Request Draft: Feature

## Title

Add historical snapshot and range-based campaign statistics

## Summary

This PR adds a historical analysis workflow for campaign results.

It introduces:

- a new API endpoint for historical campaign statistics
- two analysis modes:
  - `snapshot`: cumulative stage counts up to a cutoff time
  - `range`: recipients who first reached a stage within a selected window
- a small results-page UI for applying historical analysis without changing the
  existing default dashboard behavior

## Motivation

Gophish currently exposes:

- final-status dashboard rollups from `results.status`
- raw stored timeline events

But it does not provide a first-class way to answer questions like:

- "How many recipients had opened by date X?"
- "How many first clicked during this reporting window?"

This PR adds a minimal way to answer those questions directly in the platform.

## API

New endpoint:

- `GET /api/campaigns/:id/range-stats?mode=snapshot&end=<RFC3339>`
- `GET /api/campaigns/:id/range-stats?mode=range&start=<RFC3339>&end=<RFC3339>`

Response includes:

- `actual`: event-derived historical counts
- `dashboard`: current final-status rollup for comparison

## UI

Adds a `Historical Analysis` panel to the campaign results page with:

- `Current Dashboard` vs `Historical Events`
- `Snapshot At End` vs `First Reached In Range`
- start/end datetime pickers
- apply/reset controls
- comparison summary

## Testing

```bash
go test ./models -check.f 'TestGetCampaignRangeStatsSnapshot|TestGetCampaignRangeStatsRange'
go test ./controllers/api -run TestCampaignRangeStats
go test ./...
```

## Compatibility

- Default page behavior remains unchanged
- Historical analysis only applies when explicitly selected by the user
- No new external runtime dependencies were added
