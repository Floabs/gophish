# Suggested Upstream Issue

## Title

Silent event persistence failures can desynchronize campaign dashboard counts
from exported timeline data

## Summary

I found a real bug in the campaign event update path.

Before the fix, `models/result.go:createEvent` called `AddEvent(...)` and
ignored its error. If the event row failed to persist, the later handler could
still update `results.status` and `results.modified_date`.

That creates a state where:

- the dashboard count increases because it is derived from `results.status`
- the exported `timeline` is missing the corresponding event row

This makes historical analysis from `/api/campaigns/:id/results` impossible to
reconcile with the dashboard for affected recipients.

## Why this matters

There are already two intentional counting semantics in Gophish:

- dashboard rollup from final `results.status`
- raw stored events in `timeline`

The bug introduces a third, unintended state:

- final status changed, but no stored event exists

That is what can produce larger gaps even after deduplicating
`Email Opened`, `Clicked Link`, and `Submitted Data`.

## Reproduction

1. Create a campaign and get a `Result`.
2. Force event persistence to fail.
   - In my regression test I temporarily rename the `events` table.
3. Call `HandleEmailOpened(...)`.
4. Before the fix:
   - the method returns `nil`
   - the result status advances
   - no event row is stored
5. After the fix:
   - the method returns an error
   - the result status does not advance

## Fix

Propagate the error from `AddEvent(...)` in `createEvent(...)` and abort the
result status transition when the event cannot be written.

## Additional improvement

I also found that `GetCampaignResults(...)` returned events without an explicit
`ORDER BY`. I fixed that separately by ordering the timeline with
`time asc, id asc`, which makes historical cutoff/range analysis deterministic.
