# main.py
from fastapi import FastAPI, HTTPException, Request
import sqlite3
import os
import re

app = FastAPI()

# Use env var if set (for deployment), else local data.db
DB_PATH = os.environ.get("DATA_DB", "api/data.db")

ALLOWED_MEASURES = {
    "Violent crime rate",
    "Unemployment",
    "Children in poverty",
    "Diabetic screening",
    "Mammography screening",
    "Preventable hospital stays",
    "Uninsured",
    "Sexually transmitted infections",
    "Physical inactivity",
    "Adult obesity",
    "Premature Death",
    "Daily fine particulate matter"
}

def validate_zip(z: str) -> bool:
    return bool(re.fullmatch(r"\d{5}", z))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.post("/county_data")
async def county_data(request: Request):
    # 1) Parse JSON
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # 2) Special case: coffee=teapot -> 418
    if payload.get("coffee") == "teapot":
        raise HTTPException(status_code=418, detail="I'm a teapot")

    # 3) Validate required inputs
    if "zip" not in payload or "measure_name" not in payload:
        raise HTTPException(status_code=400, detail="zip and measure_name are required")

    z = str(payload["zip"]).strip()
    measure = str(payload["measure_name"]).strip()

    if not validate_zip(z):
        raise HTTPException(status_code=400, detail="zip must be 5 digits")
    if measure not in ALLOWED_MEASURES:
        raise HTTPException(status_code=400, detail="Invalid measure_name")

    # 4) Query DB safely (parameterized)
    conn = get_db_connection()
    cur = conn.cursor()

    # Find all county rows for this zip
    cur.execute("SELECT county, state_abbreviation, county_code FROM zip_county WHERE zip = ?", (z,))
    zip_rows = cur.fetchall()
    if not zip_rows:
        conn.close()
        raise HTTPException(status_code=404, detail="zip not found")

    results = []

    for zr in zip_rows:
        county = zr["county"]
        state_abbr = zr["state_abbreviation"]
        county_code = zr["county_code"]

        # First try by county_code (most precise)
        cur.execute("""
            SELECT state, county, state_code, county_code, year_span, measure_name, measure_id,
                   numerator, denominator, raw_value, confidence_interval_lower_bound,
                   confidence_interval_upper_bound, data_release_year, fipscode
            FROM county_health_rankings
            WHERE measure_name = ? AND county_code = ?
        """, (measure, county_code))
        rows = cur.fetchall()

        # Fallback to county + state match if needed
        if not rows:
            cur.execute("""
                SELECT state, county, state_code, county_code, year_span, measure_name, measure_id,
                       numerator, denominator, raw_value, confidence_interval_lower_bound,
                       confidence_interval_upper_bound, data_release_year, fipscode
                FROM county_health_rankings
                WHERE measure_name = ? AND county = ? AND (state = ? OR state_code = ?)
            """, (measure, county, state_abbr, state_abbr))
            rows = cur.fetchall()

        for r in rows:
            # Convert Row -> dict of strings (matches sample format)
            results.append({k: (str(r[k]) if r[k] is not None else "") for k in r.keys()})

    conn.close()

    if not results:
        # Spec: zip/measure_name combo not found -> 404
        raise HTTPException(status_code=404, detail="No data for that zip/measure_name")

    return results
