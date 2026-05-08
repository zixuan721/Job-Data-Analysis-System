"""
Data preprocessing module for job market EDA.
Can be run standalone to process raw CSV/SQLite data.

Usage:
    python analysis/preprocess.py --input data/jobs.csv --output data/processed/
    python analysis/preprocess.py --sqlite db.sqlite3 --table job_jobdata
"""

import os
import re
import csv
import json
import sqlite3
import argparse
from collections import Counter


# ─── Constants ────────────────────────────────────────────────────────────────

EXP_ORDER = ['不限', '1年以内', '1-3年', '3-5年', '5-10年', '10年以上']

EDU_ORDER = ['不限', '大专', '本科', '硕士', '博士']

SKILL_LIST = [
    'Python', 'Java', 'C++', 'JavaScript', 'TypeScript', 'React', 'Vue',
    'Angular', 'Node.js', 'Django', 'Flask', 'Spring', 'MySQL', 'Oracle',
    'MongoDB', 'Redis', 'Docker', 'Kubernetes', 'Linux', 'Git',
    '机器学习', '深度学习', '数据分析', '大数据', 'Hadoop', 'Spark',
    '前端', '后端', '全栈', '测试', '运维', '产品', 'SQL', 'R语言',
    'TensorFlow', 'PyTorch', 'Tableau', 'Power BI', '爬虫',
]


# ─── Salary parsing ───────────────────────────────────────────────────────────

def parse_salary(salary_str):
    """
    Parse a salary range string to (min_k, max_k, avg_k).

    Examples:
        '15-25K'  → (15.0, 25.0, 20.0)
        '10-20k'  → (10.0, 20.0, 15.0)
        '30K以上' → (30.0, None, 30.0)
        '面议'    → (None, None, None)
    """
    if not salary_str:
        return None, None, None
    salary_str = salary_str.strip()
    # Range pattern: 15-25K
    m = re.search(r'(\d+)[–\-](\d+)\s*[Kk]', salary_str)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        return lo, hi, round((lo + hi) / 2.0, 1)
    # Single value: 30K以上
    m2 = re.search(r'(\d+)\s*[Kk]', salary_str)
    if m2:
        v = float(m2.group(1))
        return v, None, v
    return None, None, None


# ─── Experience normalisation ─────────────────────────────────────────────────

def normalize_experience(exp_str):
    """Map raw experience string to one of EXP_ORDER categories."""
    if not exp_str or exp_str.strip() in ('不限', ''):
        return '不限'
    for label in EXP_ORDER:
        if label in exp_str or exp_str in label:
            return label
    # Fallback: try to classify by numbers
    nums = re.findall(r'\d+', exp_str)
    if nums:
        v = int(nums[0])
        if v == 0:
            return '1年以内'
        if v <= 1:
            return '1年以内'
        if v <= 3:
            return '1-3年'
        if v <= 5:
            return '3-5年'
        if v <= 10:
            return '5-10年'
        return '10年以上'
    return exp_str


# ─── City cleaning ────────────────────────────────────────────────────────────

def clean_city(place_str):
    """
    Extract top-level city from a place string.

    '北京-朝阳区' → '北京'
    '上海市浦东新区' → '上海'
    """
    if not place_str:
        return ''
    city = place_str.split('-')[0].strip()
    city = re.sub(r'市$', '', city).strip()
    return city


# ─── Skill extraction ─────────────────────────────────────────────────────────

def extract_skills(text, skill_list=None):
    """Return list of skills found in text."""
    if skill_list is None:
        skill_list = SKILL_LIST
    if not text:
        return []
    found = []
    text_lower = text.lower()
    for skill in skill_list:
        if skill.lower() in text_lower:
            found.append(skill)
    return found


# ─── Record preprocessing ────────────────────────────────────────────────────

def preprocess_record(row):
    """
    Enrich a single job record dict with derived fields.

    Adds: city, salary_min, salary_max, avg_salary, exp_norm, skills
    """
    sal_min, sal_max, sal_avg = parse_salary(row.get('salary', ''))
    text = (row.get('name', '') or '') + ' ' + (row.get('label', '') or '')
    return {
        **row,
        'city': clean_city(row.get('place', '')),
        'salary_min': sal_min,
        'salary_max': sal_max,
        'avg_salary': sal_avg,
        'exp_norm': normalize_experience(row.get('experience', '')),
        'skills': extract_skills(text),
    }


# ─── I/O helpers ─────────────────────────────────────────────────────────────

def load_csv(path):
    """Load job records from a CSV file."""
    records = []
    with open(path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(dict(row))
    return records


_ALLOWED_TABLES = frozenset({'job_jobdata', 'jobdata', 'jobs'})

_ALLOWED_QUERIES = {name: 'SELECT * FROM ' + name for name in _ALLOWED_TABLES}


def load_sqlite(db_path, table='job_jobdata'):
    """Load job records from a SQLite database table."""
    if table not in _ALLOWED_TABLES:
        raise ValueError(
            f"Table '{table}' is not in the allowlist {_ALLOWED_TABLES}. "
            "Only known job data tables may be queried."
        )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(_ALLOWED_QUERIES[table])
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def save_processed(records, output_dir):
    """Save processed records and summary statistics to output_dir."""
    os.makedirs(output_dir, exist_ok=True)

    # Full processed records
    out_path = os.path.join(output_dir, 'jobs_processed.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f'Saved {len(records)} records → {out_path}')

    # Summary statistics
    sal_vals = [r['avg_salary'] for r in records if r['avg_salary'] is not None]
    city_counts = Counter(r['city'] for r in records if r['city'])
    skill_counts = Counter(sk for r in records for sk in r['skills'])
    exp_counts = Counter(r['exp_norm'] for r in records)
    edu_counts = Counter(r.get('education', '') for r in records)

    summary = {
        'total': len(records),
        'salary': {
            'avg': round(sum(sal_vals) / len(sal_vals), 1) if sal_vals else 0,
            'min': round(min(sal_vals), 1) if sal_vals else 0,
            'max': round(max(sal_vals), 1) if sal_vals else 0,
        },
        'top_cities': dict(city_counts.most_common(20)),
        'top_skills': dict(skill_counts.most_common(30)),
        'experience_dist': {k: exp_counts.get(k, 0) for k in EXP_ORDER},
        'education_dist': {k: edu_counts.get(k, 0) for k in EDU_ORDER},
    }
    stats_path = os.path.join(output_dir, 'summary.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f'Summary statistics → {stats_path}')

    return summary


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Preprocess job market data for EDA.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--input', help='Path to input CSV file')
    group.add_argument('--sqlite', help='Path to SQLite database file')
    parser.add_argument('--table', default='job_jobdata', help='SQLite table name (default: job_jobdata)')
    parser.add_argument('--output', default='analysis/data/processed', help='Output directory')
    args = parser.parse_args()

    if args.input:
        print(f'Loading CSV: {args.input}')
        raw = load_csv(args.input)
    else:
        print(f'Loading SQLite: {args.sqlite} / table={args.table}')
        raw = load_sqlite(args.sqlite, args.table)

    print(f'Loaded {len(raw)} raw records')
    processed = [preprocess_record(r) for r in raw]
    summary = save_processed(processed, args.output)
    # Print count-only summary; detailed stats are in the output JSON file
    print('\n=== Summary ===')
    print(f'Total jobs    : {summary["total"]}')
    print(f'Unique cities : {len(summary["top_cities"])}')
    print(f'Unique skills : {len(summary["top_skills"])}')
    print(f'Full stats written to: {args.output}')


if __name__ == '__main__':
    main()
