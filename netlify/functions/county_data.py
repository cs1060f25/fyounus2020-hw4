import json
import sqlite3
import os
import re

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "api", "data.db")

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

def validate_zip(z):
    return bool(re.fullmatch(r"\d{5}", z))

def handler(event, context):
    try:
        # Parse JSON body
        body = json.loads(event.get('body', '{}'))
        
        # Check for coffee=teapot
        if body.get("coffee") == "teapot":
            return {
                'statusCode': 418,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "I'm a teapot"})
            }
        
        # Validate required fields
        if "zip" not in body or "measure_name" not in body:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "zip and measure_name are required"})
            }
        
        zip_code = str(body["zip"]).strip()
        measure = str(body["measure_name"]).strip()
        
        if not validate_zip(zip_code):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "zip must be 5 digits"})
            }
        
        if measure not in ALLOWED_MEASURES:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Invalid measure_name"})
            }
        
        # Query database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Find counties for this zip
        cur.execute("SELECT county, state_abbreviation, county_code FROM zip_county WHERE zip = ?", (zip_code,))
        zip_rows = cur.fetchall()
        
        if not zip_rows:
            conn.close()
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "zip not found"})
            }
        
        results = []
        for zr in zip_rows:
            county = zr["county"]
            state_abbr = zr["state_abbreviation"] 
            county_code = zr["county_code"]
            
            # Query health data
            cur.execute("""
                SELECT state, county, state_code, county_code, year_span, measure_name, measure_id,
                       numerator, denominator, raw_value, confidence_interval_lower_bound,
                       confidence_interval_upper_bound, data_release_year, fipscode
                FROM county_health_rankings
                WHERE measure_name = ? AND county_code = ?
            """, (measure, county_code))
            rows = cur.fetchall()
            
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
                results.append({k: (str(r[k]) if r[k] is not None else "") for k in r.keys()})
        
        conn.close()
        
        if not results:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "No data for that zip/measure_name"})
            }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(results)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": str(e)})
        }
