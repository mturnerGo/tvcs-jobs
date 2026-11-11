import json
from collections import Counter
import re

with open('jobs_data.json', encoding='utf-8') as f:
    jobs = json.load(f)

words = []
stop = {'and', 'the', 'for', 'with', 'in', 'of', 'to', 'at', 'a', 'or', 'on', 'is', 'as', 'an', 'by', 'be', 'are', 'this', 'that', 'our', 'all', 'from', 'category', 'villages', 'health'}
for j in jobs:
    text = f"{j['Job_Title']} {j['Company']} {j.get('Description', '')} {j.get('Plaza_Location', '')}".lower()
    tokens = re.findall(r'[a-zA-Z]{3,}', text)
    words.extend([t for t in tokens if t not in stop])

common = Counter(words).most_common(40)
for w, c in common:
    print(f"{w}: {c}")
