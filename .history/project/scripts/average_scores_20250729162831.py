import os
import json
import re
from bs4 import BeautifulSoup

def extract_scores_from_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    match = re.search(r'window\.__LIGHTHOUSE_JSON__\s*=\s*(\{.*?\});', html, re.DOTALL)
    if not match:
        return {}

    try:
        lighthouse_json = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}

    scores = {}
    if 'categories' in lighthouse_json:
        for key, category in lighthouse_json['categories'].items():
            scores[key] = category.get('score', 0)
    else:
        audit_scores = [
            v.get('score') for v in lighthouse_json.get('audits', {}).values()
            if isinstance(v.get('score'), (int, float))
        ]
        if audit_scores:
            scores['average'] = sum(audit_scores) / len(audit_scores)

    return scores

def walk_and_average_scores(root_path, base_path=None, limit=None, offset=0, compute_average=True):
    if base_path is None:
        base_path = root_path

    all_scores = []
    per_page_scores = []
    total_found = 0
    total_skipped = 0

    def limited_index_files(root_path):
        for root, dirs, files in os.walk(root_path):
            for file in files:
                if file == "index.html":
                    yield os.path.join(root, file)

    for full_path in limited_index_files(root_path):
        if total_skipped < offset:
            total_skipped += 1
            continue

        if limit is not None and len(per_page_scores) >= limit:
            break

        scores = extract_scores_from_html(full_path)
        if scores:
            rel_path = os.path.relpath(full_path, base_path).replace("\\", "/")
            if compute_average:
                all_scores.append(scores)

            per_page_scores.append({
                "path": rel_path,
                "scores": scores
            })

        total_found += 1

    averaged = {}
    if compute_average and all_scores:
        keys = all_scores[0].keys()
        for key in keys:
            values = [s[key] for s in all_scores if key in s]
            averaged[key] = round(sum(values) / len(values), 2) if values else 0

    # Only print debug if running as script
    if __name__ == "__main__":
        print(f"[DEBUG] Skipped: {total_skipped}, Loaded: {len(per_page_scores)}, Limit: {limit}, Offset: {offset}")

    return {
        "average": averaged if compute_average else None,
        "pages": per_page_scores
    }

if __name__ == "__main__":
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    REPORTS_ROOT = os.path.join(BASE_DIR, '..', 'static', 'reports', 'lighthouse_reports')
    result = walk_and_average_scores(REPORTS_ROOT)
    print(json.dumps(result))  # ✅ Output clean JSON
