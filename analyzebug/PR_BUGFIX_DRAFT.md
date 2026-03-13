# Pull Request Draft: Bug Fix

## Title

Propagate event persistence errors and return campaign events in deterministic order

## Summary

This PR fixes a campaign tracking inconsistency where a result status could be
updated even if the corresponding event failed to persist.

It also makes campaign timeline exports deterministic by ordering returned
events with `time asc, id asc`.

## Problem

Campaign dashboards are derived from `results.status`, while historical exports
use stored `timeline` events.

Before this change:

- `createEvent(...)` ignored `AddEvent(...)` errors
- a result could advance to `Email Opened`, `Clicked Link`, or `Submitted Data`
  even if no event row was written
- this caused dashboards to over-report compared to the stored timeline

Separately, `GetCampaignResults(...)` returned events without an explicit
ordering clause, which made historical analysis depend on database row order.

## Changes

- propagate `AddEvent(...)` errors in `models/result.go`
- stop status transitions when the event write fails
- order campaign events by `time asc, id asc` in `GetCampaignResults(...)`
- add regression tests for:
  - status not updating when event persistence fails
  - deterministic event ordering in campaign results

## Testing

```bash
go test ./models -check.f 'TestGetCampaignResultsOrdersEvents|TestHandleEmailOpenedDoesNotUpdateResultWhenEventSaveFails'
go test ./...
```

## Why keep this PR focused

This PR intentionally fixes correctness only.

Historical range/snapshot analysis and UI support were implemented locally as a
separate enhancement, but are not required for the correctness bug fix itself.
