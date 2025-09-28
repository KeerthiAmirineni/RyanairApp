# Ryanair Booking Automation

Automates Ryanair flight booking using Python and Playwright. Configurable via JSON file.

## Quick Start

```bash
# Install dependencies
pip install playwright
playwright install

# Run the script
python book_ryanair.py
```

## Running on Docker
1. docker build -t my-ryanair-demo-app .
2. docker run my-ryanair-demo-app


## What It Does
1. Opens Ryanair and accepts cookies
2. Fills flight details from config.json
3. Searches and selects flights
4. Fills passenger details
5. Selects seats and adds bags
6. Pauses before payment for review

## Configuration

Edit `config.json` with your booking details:

```json
{
  "flight_details": {
    "departure_airport": "London Gatwick",
    "departure_code": "LGW",
    "destination_airport": "Dublin", 
    "destination_code": "DUB",
    "departure_date": "2025-10-15",
    "return_date": "2025-10-22"
  },
  "passengers": {
    "adults": [
      {"title": "Mr", "first_name": "John", "surname": "Smith"}
    ]
  },
  "browser_settings": {
    "headless": false
  }
}

## Important Notes

- Supports up to 2 adult passengers  
- Uses IATA airport codes (DUB, LGW, etc.)
- Dates must be YYYY-MM-DD format
- Set `"headless": false` to watch the browser
- Script stops before payment for review

**Disclaimer**: Testing purposes only.