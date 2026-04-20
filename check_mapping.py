import csv
import hashlib
from pathlib import Path

sources_path = Path('data/sources.csv')
url_mapping = {}

with open(sources_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        source_url = row.get('source_url', '')
        if source_url:
            url_hash = hashlib.md5(source_url.encode('utf-8')).hexdigest()[:12]
            filename = f'{url_hash}.html'
            url_mapping[filename] = source_url
            print(f'{filename} -> {source_url}')

print(f'\nTotal URLs in mapping: {len(url_mapping)}')

# Check actual files in raw directory
raw_files = list(Path('data/raw').glob('*.html'))
print(f'\nActual files in data/raw: {len(raw_files)}')
for f in sorted(raw_files):
    print(f'  - {f.name}')
