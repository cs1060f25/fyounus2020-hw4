#!/usr/bin/env python3
"""
csv_to_sqlite.py
Usage:
    python3 csv_to_sqlite.py data.db zip_county.csv
    python3 csv_to_sqlite.py data.db county_health_rankings.csv

Creates (or opens) the sqlite3 database and creates a table named after the CSV filename
(without extension). All columns are created as TEXT. Header names are sanitized into valid
SQL identifiers (letters, digits, underscore). Insertion uses parameterized SQL.
"""
import argparse
import csv
import os
import re
import sqlite3
import sys

def sanitize_identifier(name):
    # Lowercase, replace spaces and other non-alnum with underscores, collapse multiple underscores.
    s = name.strip()
    s = s.replace('-', '_')
    s = re.sub(r'\s+', '_', s)
    # keep only letters, digits, underscore
    s = re.sub(r'[^0-9a-zA-Z_]', '', s)
    # ensure it doesn't start with digit
    if re.match(r'^[0-9]', s):
        s = '_' + s
    if s == '':
        s = 'col'
    return s.lower()

def table_name_from_path(path):
    base = os.path.basename(path)
    name = os.path.splitext(base)[0]
    # sanitize table name similarly
    name = re.sub(r'[^0-9a-zA-Z_]', '_', name)
    if re.match(r'^[0-9]', name):
        name = '_' + name
    return name.lower()

def create_table_and_insert(conn, table_name, headers, rows):
    cur = conn.cursor()
    cols = [sanitize_identifier(h) for h in headers]
    # ensure unique column names (append _n if duplicates)
    seen = {}
    for i, c in enumerate(cols):
        if c in seen:
            seen[c] += 1
            cols[i] = f"{c}_{seen[c]}"
        else:
            seen[c] = 0

    col_defs = ', '.join([f"{c} TEXT" for c in cols])
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({col_defs});"
    cur.execute(create_sql)

    placeholders = ','.join(['?'] * len(cols))
    insert_sql = f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({placeholders});"

    # Insert all rows
    for row in rows:
        # If row shorter than headers, pad with empty strings; if longer, truncate
        vals = row[:len(cols)] + [''] * max(0, len(cols) - len(row))
        cur.execute(insert_sql, vals)
    conn.commit()

def main():
    parser = argparse.ArgumentParser(description="CSV -> SQLite loader")
    parser.add_argument('db', help='sqlite3 database filename to create/use')
    parser.add_argument('csvfile', help='CSV file to import (header row required)')
    args = parser.parse_args()

    if not os.path.exists(args.csvfile):
        print(f"CSV file not found: {args.csvfile}", file=sys.stderr)
        sys.exit(2)

    table_name = table_name_from_path(args.csvfile)

    with open(args.csvfile, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            print("CSV file appears empty", file=sys.stderr)
            sys.exit(2)
        rows = [r for r in reader]

    conn = sqlite3.connect(args.db)
    try:
        create_table_and_insert(conn, table_name, headers, rows)
    finally:
        conn.close()
    print(f"Imported {len(rows)} rows into table '{table_name}' in {args.db}")

if __name__ == '__main__':
    main()
