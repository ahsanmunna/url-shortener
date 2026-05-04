from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from datetime import datetime
from utils import strip_trackers, generate_short_code, generate_qr_code
from models import ShortenRequest, VerifyRequest
from database import get_connection

app = FastAPI()

@app.post("/shorten")
def shorten_url(request: ShortenRequest):
    cleaned_url, removed_trackers = strip_trackers(str(request.original_url))
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        while True:
            short_code = generate_short_code()
            cur.execute("SELECT id FROM links WHERE short_code = %s", (short_code,))
            if cur.fetchone() is None:
                break

        short_url = f"https://your-domain/{short_code}"
        qr_code = generate_qr_code(short_url)

        cur.execute("""
            INSERT INTO links (
                original_url,
                short_code,
                is_ghost,
                password,
                click_limit,
                expiry_date,
                stripped_trackers,
                qr_code,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            cleaned_url,
            short_code,
            request.is_ghost,
            request.password,
            request.click_limit,
            request.expiry_date,
            removed_trackers,
            qr_code
        ))
        conn.commit()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return {"short_url": short_url, "qr_code": qr_code}

@app.post("/verify/{short_code}")
def verify_url(short_code: str, request: VerifyRequest):
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, original_url, password, is_active FROM links WHERE short_code = %s",
            (short_code,)
        )
        row = cur.fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Short URL not found")

        link_id, original_url, stored_password, is_active = row

        if not is_active:
            raise HTTPException(status_code=410, detail="This link has expired")

        if request.password != stored_password:
            raise HTTPException(status_code=401, detail="Wrong password")

        cur.execute(
            "INSERT INTO clicks (link_id, device_info, ip_address, timestamp_click) VALUES (%s, %s, %s, NOW())",
            (link_id, None, None)
        )
        conn.commit()
    finally:
        if cur: cur.close()
        if conn: conn.close()

    return {"original_url": original_url}

@app.get("/analytics/{short_code}")
def get_analytics(short_code: str):
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, original_url FROM links WHERE short_code = %s",
            (short_code,)
        )
        link = cur.fetchone()

        if link is None:
            raise HTTPException(status_code=404, detail="Short URL not found")

        link_id = link[0]
        original_url = link[1]

        cur.execute(
            "SELECT COUNT(*) FROM clicks WHERE link_id = %s",
            (link_id,)
        )
        total_clicks = cur.fetchone()[0]

        cur.execute(
            "SELECT id, device_info, ip_address, timestamp_click FROM clicks WHERE link_id = %s ORDER BY timestamp_click DESC",
            (link_id,)
        )
        rows = cur.fetchall()
        click_details = [
            {
                "id": row[0],
                "device_info": row[1],
                "ip_address": row[2],
                "timestamp_click": row[3]
            }
            for row in rows
        ]

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return {
        "short_code": short_code,
        "original_url": original_url,
        "total_clicks": total_clicks,
        "clicks": click_details
    }

@app.get("/{short_code}")
def redirect_url(short_code: str, request: Request):
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, original_url, is_ghost, is_active, expiry_date, click_limit, password FROM links WHERE short_code = %s",
            (short_code,)
        )
        row = cur.fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Short URL not found")

        link_id, original_url, is_ghost, is_active, expiry_date, click_limit, password = row

        if password is not None:
            return {"protected": True}

        if not is_active:
            raise HTTPException(status_code=410, detail="This link has expired")

        if expiry_date and datetime.now() > expiry_date:
            cur.execute("UPDATE links SET is_active = FALSE WHERE id = %s", (link_id,))
            conn.commit()
            raise HTTPException(status_code=410, detail="This link has expired")

        if click_limit is not None:
            cur.execute("SELECT COUNT(*) FROM clicks WHERE link_id = %s", (link_id,))
            total_clicks = cur.fetchone()[0]
            if total_clicks >= click_limit:
                cur.execute("UPDATE links SET is_active = FALSE WHERE id = %s", (link_id,))
                conn.commit()
                raise HTTPException(status_code=410, detail="This link has reached its click limit")

        device_info = request.headers.get("user-agent")
        ip_address = request.headers.get("x-forwarded-for") or request.client.host

        cur.execute(
            "INSERT INTO clicks (link_id, device_info, ip_address, timestamp_click) VALUES (%s, %s, %s, NOW())",
            (link_id, device_info, ip_address)
        )

        if is_ghost:
            cur.execute("UPDATE links SET is_active = FALSE WHERE id = %s", (link_id,))

        conn.commit()

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return RedirectResponse(url=original_url, status_code=302)