
import requests
from urllib.parse import urlparse

ENDPOINT = "https://link-checker.nordvpn.com/v1/public-url-checker/check-url"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://nordvpn.com",
    "Referer": "https://nordvpn.com/",
}
TIMEOUT = 15

def validate_url(u):
    parsed = urlparse(u)
    if not parsed.scheme:
        return "https://" + u
    return u

def _do_post(session, url, payload):
    try:
        return session.post(url, headers=HEADERS, json=payload, timeout=TIMEOUT)
    except requests.RequestException:
        return None

def _get_verdict(resp):
    try:
        data = resp.json()
    except Exception:
        return "فشل الفحص "

    status = data.get("status")
    category = data.get("category")

    if status != 0:
        return "فشل الفحص "
    if category in (0, 1, "0", "1"):
        return "آمن "
    elif category in (2, 3, "2", "3"):
        return "مشتبه "
    elif category in (4, 5, "4", "5"):
        return "خبيث ❌"
    else:
        return "آمن إلى حد ما "

def check_url(input_url):
    input_url = validate_url(input_url)
    session = requests.Session()
    payload = {"url": input_url}
    resp = _do_post(session, ENDPOINT, payload)
    verdict = _get_verdict(resp) if resp else "فشل الاتصال "
    return verdict

