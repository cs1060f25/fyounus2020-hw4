from fastapi import FastAPI, HTTPException, Request
import sqlite3, os, re
from starlette.responses import JSONResponse
from asgiref.wsgi import WsgiToAsgi  # <-- adapter

app = FastAPI()

DB_PATH = os.path.join(os.path.dirname(__file__), "data.sqlite")

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
    "Daily fine particulate matter",
}

def validate_zip(z: str) -> bool:
    return bool(re.fullmatch(r"\d{5}", z))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.post("/")
async def county_data(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if payload.get("coffee") == "teapot":
        raise HTTPException(status_code=418, detail="I'm a teapot")

    if "zip" not in payload or "measure_name" not in payload:
        raise HTTPException(status_code=400, detail="zip and measure_name are required")

    z = str(payload["zip"]).strip()
    measure = str(payload["measure_name"]).strip()

    if not validate_zip(z):
        raise HTTPException(status_code=400, detail="zip must be 5 digits")
    if measure not in ALLOWED_MEASURES:
        raise HTTPException(status_code=400, detail="Invalid measure_name")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT county, state_abbreviation, county_code FROM zip_county WHERE zip = ?", (z,))
    zip_rows = cur.fetchall()
    if not zip_rows:
        conn.close()
        raise HTTPException(status_code=404, detail="zip not found")

    results = []
    for zr in zip_rows:
        county, state_abbr, county_code = zr["county"], zr["state_abbreviation"], zr["county_code"]

        cur.execute("SELECT * FROM county_health_rankings WHERE measure_name = ? AND county_code = ?", (measure, county_code))
        rows = cur.fetchall()

        if not rows:
            cur.execute("""SELECT * FROM county_health_rankings
                           WHERE measure_name = ? AND county = ? AND (state = ? OR state_code = ?)""",
                        (measure, county, state_abbr, state_abbr))
            rows = cur.fetchall()

        for r in rows:
            results.append({k: (str(r[k]) if r[k] is not None else "") for k in r.keys()})

    conn.close()

    if not results:
        raise HTTPException(status_code=404, detail="No data for that zip/measure_name")

    return results

# Vercel requires a variable named "handler" for serverless functions.
# FastAPI is ASGI, so we expose it directly.
handler = app
