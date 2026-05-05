# URL Shortener — Privacy First

A backend API that shortens URLs without tracking you. No signups, no data collection, no surveillance capitalism.

## What Makes This Different

Most URL shorteners are data collection tools disguised as utilities. This one strips tracking parameters (fbclid, utm_source, etc.) from your links automatically, so the destination never knows where you came from.

## Features

- **Tracker stripping** — removes fbclid, utm_source, utm_campaign and more automatically
- **Ghost links** — self-destruct after one click
- **Link expiry** — expire by date or click count
- **Password protection** — restrict access to people who know the password
- **QR code generation** — every link gets a QR code automatically
- **Click analytics** — track clicks, devices, and timestamps

## Tech Stack

- **FastAPI** — Python web framework
- **PostgreSQL** — database
- **psycopg2** — database driver
- **Pydantic** — input validation
- **Python-dotenv** — environment variable management

## Setup & Installation

1. Clone the repository
```
   git clone https://github.com/ahsanmunna/url-shortener.git
   cd url-shortener
```

2. Create virtual environment
```
   python -m venv venv
   venv\Scripts\activate
```

3. Install dependencies
```
   pip install -r requirements.txt
```

4. Create a `.env` file
```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=url_shortener
   DB_USER=postgres
   DB_PASSWORD=yourpassword
```

5. Run the server
```
   uvicorn main:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/shorten` | Shorten a URL |
| GET | `/{short_code}` | Redirect to original URL |
| GET | `/analytics/{short_code}` | Get click analytics |
| POST | `/verify/{short_code}` | Verify password for protected links |

## Example Request

```json
{
    "original_url": "https://facebook.com/profile?fbclid=abc123&utm_source=facebook",
    "is_ghost": false,
    "click_limit": 10,
    "expiry_date": "2026-12-31T00:00:00",
    "password": "optional"
}
```

## Example Response

```json
{
    "short_url": "https://your-domain/x7Kp2m",
    "qr_code": "base64encodedimage..."
}
```
