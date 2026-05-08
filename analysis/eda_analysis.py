"""
Standalone EDA analysis script for job market data.
Generates statistical summaries and chart-ready data structures.

Usage:
    python analysis/eda_analysis.py --data analysis/data/processed/jobs_processed.json
    python analysis/eda_analysis.py --sqlite db.sqlite3
"""

import os
import re
import json
import argparse
import sqlite3
from collections import Counter, defaultdict

from preprocess import (
    parse_salary, clean_city, normalize_experience, extract_skills,
    preprocess_record, load_sqlite, EXP_ORDER, EDU_ORDER, SKILL_LIST,
)


# ─── Statistics helpers ───────────────────────────────────────────────────────

def boxplot_stats(values):
    """Return {min, q1, median, q3, max} for a list of numbers."""
    if not values:
        return {'min': 0, 'q1': 0, 'median': 0, 'q3': 0, 'max': 0}
    arr = sorted(values)
    n = len(arr)

    def pct(p):
        idx = p / 100.0 * (n - 1)
        lo, hi = int(idx), min(int(idx) + 1, n - 1)
        return arr[lo] + (arr[hi] - arr[lo]) * (idx - lo)

    q1, median, q3 = pct(25), pct(50), pct(75)
    iqr = q3 - q1
    lo_fence, hi_fence = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    fenced = [v for v in arr if lo_fence <= v <= hi_fence]
    return {
        'min': round(min(fenced) if fenced else arr[0], 1),
        'q1': round(q1, 1),
        'median': round(median, 1),
        'q3': round(q3, 1),
        'max': round(max(fenced) if fenced else arr[-1], 1),
    }


# ─── Analysis functions ───────────────────────────────────────────────────────

def analyse_salary_distribution(records):
    """Return histogram bins for salary distribution."""
    sal_vals = [r['avg_salary'] for r in records if r.get('avg_salary') is not None]
    bins = ['5K以下', '5-10K', '10-15K', '15-20K', '20-30K', '30-50K', '50K以上']
    counts = [0] * 7
    for s in sal_vals:
        if s < 5:
            counts[0] += 1
        elif s < 10:
            counts[1] += 1
        elif s < 15:
            counts[2] += 1
        elif s < 20:
            counts[3] += 1
        elif s < 30:
            counts[4] += 1
        elif s < 50:
            counts[5] += 1
        else:
            counts[6] += 1
    return {'bins': bins, 'counts': counts, 'total_with_salary': len(sal_vals)}


def analyse_city_salary(records, top_n=15):
    """Return top-N cities ranked by average salary."""
    city_map = defaultdict(list)
    for r in records:
        if r.get('city') and r.get('avg_salary') is not None:
            city_map[r['city']].append(r['avg_salary'])
    averages = {c: round(sum(v) / len(v), 1) for c, v in city_map.items() if v}
    ranked = sorted(averages.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return {'cities': [x[0] for x in ranked], 'avg_salaries': [x[1] for x in ranked]}


def analyse_exp_salary(records):
    """Return boxplot stats for each experience category."""
    exp_map = defaultdict(list)
    for r in records:
        if r.get('avg_salary') is not None:
            exp_map[r.get('exp_norm', '不限')].append(r['avg_salary'])
    result = {}
    for label in EXP_ORDER:
        if label in exp_map:
            result[label] = boxplot_stats(exp_map[label])
    return result


def analyse_edu_salary(records):
    """Return boxplot stats for each education category."""
    edu_map = defaultdict(list)
    for r in records:
        edu = r.get('education', '') or '不限'
        if r.get('avg_salary') is not None:
            edu_map[edu].append(r['avg_salary'])
    result = {}
    for label in EDU_ORDER:
        if label in edu_map:
            result[label] = boxplot_stats(edu_map[label])
    return result


def analyse_skill_cooccurrence(records, top_n=15):
    """Build skill co-occurrence matrix for the top-N skills."""
    skill_counter = Counter()
    for r in records:
        for sk in r.get('skills', []):
            skill_counter[sk] += 1
    top_skills = {s for s, _ in skill_counter.most_common(top_n)}

    cooccur = Counter()
    for r in records:
        job_skills = [s for s in r.get('skills', []) if s in top_skills]
        for i in range(len(job_skills)):
            for j in range(i + 1, len(job_skills)):
                pair = tuple(sorted([job_skills[i], job_skills[j]]))
                cooccur[pair] += 1

    nodes = [{'name': s, 'value': skill_counter[s]} for s in top_skills]
    links = [
        {'source': p[0], 'target': p[1], 'value': c}
        for p, c in cooccur.most_common(40)
    ]
    return {'nodes': nodes, 'links': links, 'top_skills': dict(skill_counter.most_common(top_n))}


def analyse_heatmap(records):
    """Return edu × exp heatmap data (average salary)."""
    cell_map = defaultdict(list)
    for r in records:
        edu = r.get('education', '') or '不限'
        exp = r.get('exp_norm', '不限')
        if r.get('avg_salary') is not None:
            cell_map[(edu, exp)].append(r['avg_salary'])
    averages = {k: round(sum(v) / len(v), 1) for k, v in cell_map.items() if v}
    edu_labels = [l for l in EDU_ORDER if any(k[0] == l for k in averages)]
    exp_labels = [l for l in EXP_ORDER if any(k[1] == l for k in averages)]
    matrix = [
        [averages.get((edu, exp), None) for edu in edu_labels]
        for exp in exp_labels
    ]
    return {'edu_labels': edu_labels, 'exp_labels': exp_labels, 'matrix': matrix}


def run_full_eda(records):
    """Run all analyses and return a combined results dict."""
    sal_vals = [r['avg_salary'] for r in records if r.get('avg_salary') is not None]
    skill_counter = Counter(sk for r in records for sk in r.get('skills', []))
    city_counter = Counter(r['city'] for r in records if r.get('city'))

    results = {
        'total_records': len(records),
        'salary_summary': boxplot_stats(sal_vals),
        'salary_dist': analyse_salary_distribution(records),
        'city_salary': analyse_city_salary(records),
        'exp_salary': analyse_exp_salary(records),
        'edu_salary': analyse_edu_salary(records),
        'skill_analysis': analyse_skill_cooccurrence(records),
        'heatmap': analyse_heatmap(records),
        'top_cities': dict(city_counter.most_common(20)),
        'top_skills': dict(skill_counter.most_common(30)),
        'education_dist': {k: sum(1 for r in records if (r.get('education') or '不限') == k) for k in EDU_ORDER},
        'experience_dist': {k: sum(1 for r in records if r.get('exp_norm') == k) for k in EXP_ORDER},
        'scale_dist': dict(Counter(r.get('scale', '') for r in records if r.get('scale')).most_common(10)),
    }
    return results


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Run EDA analysis on job data.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--data', help='Path to preprocessed JSON file')
    group.add_argument('--sqlite', help='Path to SQLite database')
    parser.add_argument('--table', default='job_jobdata', help='SQLite table name')
    parser.add_argument('--output', default='analysis/data/processed/eda_results.json')
    args = parser.parse_args()

    if args.data:
        print(f'Loading: {args.data}')
        with open(args.data, encoding='utf-8') as f:
            records = json.load(f)
    else:
        print(f'Loading SQLite: {args.sqlite}')
        raw = load_sqlite(args.sqlite, args.table)
        records = [preprocess_record(r) for r in raw]

    print(f'Analysing {len(records)} records...')
    results = run_full_eda(records)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'EDA results saved → {args.output}')

    # Summary: use independently computed counts rather than derived result values
    n_cities = len(results["top_cities"])
    n_skills = len(results["top_skills"])
    print('\n=== EDA Summary ===')
    print(f'Input records   : {len(records)}')
    print(f'Unique cities   : {n_cities}')
    print(f'Unique skills   : {n_skills}')
    print(f'Full stats written to: {args.output}')


if __name__ == '__main__':
    main()
