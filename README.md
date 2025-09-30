# County Health Data API - cs1060-hw4

A REST API that provides county health data based on ZIP codes and health measures. This API allows users to query health statistics for specific counties using ZIP codes and predefined health measures.

## Data Sources

This API uses two public data sources:
- **RowZero Zip Code to County**: Maps ZIP codes to counties
- **County Health Rankings & Roadmaps**: Provides health statistics by county

## API Endpoint

**POST** `/county_data`

### Request Format
```json
{
  "zip": "02138",
  "measure_name": "Adult obesity"
}
```

### Required Fields
- `zip`: 5-digit ZIP code (string)
- `measure_name`: One of the following health measures:
  - Violent crime rate
  - Unemployment
  - Children in poverty
  - Diabetic screening
  - Mammography screening
  - Preventable hospital stays
  - Uninsured
  - Sexually transmitted infections
  - Physical inactivity
  - Adult obesity
  - Premature Death
  - Daily fine particulate matter

### Response Format
Returns an array of health data records matching the ZIP code and measure:

```json
[
  {
    "state": "MA",
    "county": "Middlesex County",
    "state_code": "25",
    "county_code": "17",
    "year_span": "2009",
    "measure_name": "Adult obesity",
    "measure_id": "11",
    "numerator": "60771.02",
    "denominator": "263078",
    "raw_value": "0.23",
    "confidence_interval_lower_bound": "0.22",
    "confidence_interval_upper_bound": "0.24",
    "data_release_year": "2012",
    "fipscode": "25017"
  }
]
```

### Special Cases
- If `coffee=teapot` is included in the request, returns HTTP 418 "I'm a teapot"
- Missing required fields return HTTP 400 "Bad Request"
- Invalid ZIP/measure combinations return HTTP 404 "Not Found"

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Generate the database from CSV files:
```bash
python3 csv_to_sqlite.py data.db zip_county.csv
python3 csv_to_sqlite.py data.db county_health_rankings.csv
```

3. Run the API locally:
```bash
python3 main.py
```

## Testing

Test the API with curl:
```bash
curl -X POST https://fyounus2020-hw4.onrender.com/county_data \
  -H "Content-Type: application/json" \
  -d '{"zip":"02138","measure_name":"Unemployment"}'
```

## Deployment

This API is deployed on Render at: https://fyounus2020-hw4.onrender.com/county_data

## Development Tools Used

This project was developed with assistance from:
- **ChatGPT** for API development guidance and code structure
- **Cursor** for code editing, debugging, and deployment assistance

The `csv_to_sqlite.py` script was created with AI assistance to handle arbitrary CSV files and generate SQLite databases with proper schema sanitization.
