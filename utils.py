from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import secrets
import string
import qrcode
import io
import base64

TRACKING_PARAMS = [
    "fbclid", "utm_source", "utm_medium", "utm_campaign",
    "utm_term", "utm_content", "ref", "mc_eid"
]

def strip_trackers(url):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    trackers = [
        key for key in params.keys()
        if key in TRACKING_PARAMS
    ]
    cleaned_params = {
        key: value for key, value in params.items()
        if key not in TRACKING_PARAMS
    }
    new_query = urlencode(cleaned_params, doseq=True)
    clean_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    return clean_url, trackers


def generate_short_code(length=6):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_qr_code(url):
    img = qrcode.make(url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    return encoded