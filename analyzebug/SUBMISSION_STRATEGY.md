# Recommended Submission Strategy

For the best chance of acceptance, do not submit the entire change set as one
large PR.

## Recommended Order

### 1. Open the bug issue first

Use:

- `analyzebug/ISSUE_DRAFT.md`

Goal:

- establish the correctness problem
- show it is reproducible
- avoid mixing the bug with the feature request

### 2. Submit a small bug-fix PR

Use:

- `analyzebug/PR_BUGFIX_DRAFT.md`

Recommended scope:

- `models/result.go`
- `models/result_test.go`
- `models/campaign.go`
- `models/campaign_test.go`

Reason:

- maintainers are much more likely to merge a correctness fix with regression
  tests than a large feature/UI bundle

### 3. Open a separate feature request or PR

Use:

- `analyzebug/PR_FEATURE_DRAFT.md`

Recommended only after bug discussion:

- `models/campaign_range.go`
- `models/campaign_range_test.go`
- `controllers/api/campaign.go`
- `controllers/api/server.go`
- `controllers/api/api_test.go`
- `templates/campaign_results.html`
- `static/js/src/app/campaign_results.js`
- `static/js/src/app/gophish.js`
- corresponding built minified assets

Reason:

- it is clearly an enhancement, not a bug fix
- it changes API and UI behavior surface
- it may require maintainer feedback on naming and UX

## Commit Suggestions

### Bug fix

```text
fix: propagate campaign event persistence failures
```

### Feature

```text
feat: add historical campaign range statistics
```

## Reviewer-Friendly Practices

- keep the bug fix and feature separate
- mention exact tests you ran
- avoid unrelated lockfile or generated-file noise
- explain semantics carefully:
  - dashboard rollup
  - historical event truth
  - snapshot vs range
- keep screenshots optional unless maintainers ask

## What to Avoid

- do not frame the dashboard rollup itself as automatically wrong
- do not claim all historical mismatches are duplicates
- do not bundle docs, bug fix, API redesign, and UI redesign into a single PR
  if you want the highest merge probability
