#!/usr/bin/env python3
"""Validate and append-only sync for fingerprints.jsonl. Standard library only.

  python3 scripts/fingerprints.py check [--previous OLD_FILE]
  python3 scripts/fingerprints.py sync  [--url INDEX_URL]

`check` validates every line and, given the previous version of the file,
requires the new file to start with it unchanged. `sync` appends records that
appear in the public index and are not yet here; if any record already here
differs from the index, it fails and changes nothing.
"""
import argparse, json, re, sys, urllib.error, urllib.request
from pathlib import Path

FILE = Path(__file__).resolve().parent.parent / 'fingerprints.jsonl'
INDEX_URL = 'https://giuseppegiobbe.com/research/data/briefings/index.jsonl'
FIELDS = ('briefing_date', 'revision', 'sha256', 'bytes', 'briefing_id', 'delivery_result',
          'sections', 'data_through', 'prepared_at', 'recorded_at')
DAY = re.compile(r'^\d{4}-\d{2}-\d{2}$')
HEX = re.compile(r'^[0-9a-f]{64}$')


def canonical(record):
    """One line per record, fixed field set and order, so equal records are equal bytes."""
    return json.dumps({k: record.get(k) for k in FIELDS}, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def validate(record):
    assert set(record) == set(FIELDS), f'unexpected fields: {sorted(set(record) ^ set(FIELDS))}'
    assert DAY.match(record['briefing_date']), 'briefing_date'
    assert isinstance(record['revision'], int) and record['revision'] >= 1, 'revision'
    assert HEX.match(record['sha256']) and HEX.match(record['briefing_id']), 'hashes'
    assert isinstance(record['bytes'], int) and record['bytes'] > 0, 'bytes'
    assert record['delivery_result'] in ('complete', 'partial'), 'delivery_result'
    assert isinstance(record['sections'], dict), 'sections'
    assert record['data_through'] is None or DAY.match(record['data_through']), 'data_through'


def parse(text):
    records = []
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        validate(record)
        assert line == canonical(record), f'line {n} is not in canonical form'
        records.append(record)
    keys = [(r['briefing_date'], r['revision']) for r in records]
    assert keys == sorted(keys) and len(set(keys)) == len(keys), 'records must be unique and in date/revision order'
    return records


def check(previous):
    text = FILE.read_text()
    parse(text)
    if previous is not None:
        old = Path(previous).read_text()
        assert text.startswith(old), 'an existing line was changed or removed; this file is append-only'
    print(f'OK: {len(text.splitlines())} fingerprints, append-only')


def sync(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'briefing-fingerprints-sync/1 (+https://github.com/ggiuseppe5/briefing-fingerprints)'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            published = response.read(5_000_000).decode()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            print('Public index not available yet; nothing to sync.')
            return
        raise
    current = parse(FILE.read_text())
    have = {(r['briefing_date'], r['revision']): canonical(r) for r in current}
    new = []
    for line in published.splitlines():
        if not line.strip():
            continue
        record = {k: json.loads(line).get(k) for k in FIELDS}
        validate(record)
        key = (record['briefing_date'], record['revision'])
        if key in have:
            assert have[key] == canonical(record), f'PUBLISHED RECORD CHANGED for {key}: refusing to update'
        else:
            new.append(record)
    if not new:
        print('No new fingerprints.')
        return
    last = max(have) if have else ('', 0)
    new.sort(key=lambda r: (r['briefing_date'], r['revision']))
    assert (new[0]['briefing_date'], new[0]['revision']) > last, 'a new record is older than the last recorded one; refusing to insert'
    with FILE.open('a') as out:
        for record in new:
            out.write(canonical(record) + '\n')
    print(f'Appended {len(new)} fingerprint(s).')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    c = sub.add_parser('check'); c.add_argument('--previous')
    s = sub.add_parser('sync'); s.add_argument('--url', default=INDEX_URL)
    args = parser.parse_args()
    try:
        check(args.previous) if args.command == 'check' else sync(args.url)
    except (AssertionError, ValueError, KeyError, urllib.error.URLError) as error:
        print(f'FAILED: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
