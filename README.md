# Briefing fingerprints

A public, append-only record of the daily market briefing data published at
[giuseppegiobbe.com](https://giuseppegiobbe.com/research/briefings).

Every weekday evening (London time) the research pipeline freezes that day's
briefing data into a single JSON record and never edits it again. A correction
is saved as a new revision next to the original, never over it.

This repository holds **only the fingerprints** of those records: one line per
record in [`fingerprints.jsonl`](fingerprints.jsonl). It holds no market data,
no articles and no code from the research system.

## Why it exists

Git gives every line here a public timestamp, and a line cannot be changed later
without the change showing in the history. So anyone can check that a briefing
record existed on the day it says, and that it has not been altered since.

## What each line contains

| Field | Meaning |
| --- | --- |
| `briefing_date` | London date the briefing was prepared |
| `revision` | 1 for the original; 2, 3… for corrections saved alongside it |
| `sha256` | SHA-256 of the exact JSON record |
| `bytes` | size of the record |
| `briefing_id` | the briefing's own content identifier |
| `delivery_result` | `complete`, or `partial` when some sections could not be refreshed |
| `sections` | each section's state that day: `refreshed`, `retained` or `unavailable` |
| `data_through` | latest observation date in the record |
| `prepared_at`, `recorded_at` | when it was prepared and when it was frozen (UTC) |

## How to check a record

1. Download a day's record, for example
   `https://giuseppegiobbe.com/research/data/briefings/2026-11-13.json`.
2. Compute its SHA-256, e.g. `shasum -a 256 2026-11-13.json`.
3. It must equal the `sha256` on that day's line here, and that line must be in
   the history from that day.

## How it is updated

A scheduled workflow copies new lines from the public index at
`https://giuseppegiobbe.com/research/data/briefings/index.jsonl` after each
weekday briefing. It only ever appends. If a line already recorded here ever
differs from the published index, the workflow fails loudly instead of
changing it. Force-pushes and deletion of `main` are blocked.

## Use of the data

The fingerprints are published so the record can be verified. The briefing
data itself is published on giuseppegiobbe.com under that site's terms, which
do not permit AI training (`Content-Signal: ai-train=no`).
