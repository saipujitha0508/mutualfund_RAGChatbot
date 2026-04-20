import json
from pathlib import Path

duplicate_id = '2f5439e933365caaad37a2eff49f2b31'
removed = 0

for f in Path('data/embedded').glob('*_embedded.json'):
    with open(f, 'r', encoding='utf-8') as file:
        chunks = json.load(file)
    
    original_len = len(chunks)
    chunks = [c for c in chunks if c['chunk_id'] != duplicate_id]
    
    if len(chunks) != original_len:
        with open(f, 'w', encoding='utf-8') as out:
            json.dump(chunks, out, ensure_ascii=False, indent=2)
        removed += original_len - len(chunks)

print(f'Removed {removed} duplicate chunk(s)')
