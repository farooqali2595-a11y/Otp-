import requests
import json
import time
import re
import os
import pycountry
import phonenumbers
from flask import Flask, Response
import threading

# ================= CONFIG =================

API_TOKEN = "Qk5PSUNWfkJGUVZK"
BASE_URL = "http://137.74.1.203/crapi/reseller/mdr.php"

BOT_TOKEN = "7798354146:AAFzA28J60SBgPWqfYrt2sYaBJiYZPr5reg"
CHAT_IDS = ["-100393155399"]

SEEN_FILE = "seen.json"

# ================= STORAGE =================

def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(data)[-5000:], f)

seen = load_seen()

# ================= TELEGRAM =================

def send(msg, otp):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    keyboard = {
        "inline_keyboard": [
            [
                {"text": f"🔑 OTP: {otp}", "callback_data": f"otp_{otp}"}
            ],
            [
                {"text": "📢 NUMBER CHANNEL", "url": "https://t.me/team_AxI_Num"},
                {"text": "💬 DISCUSSION GROUP", "url": "https://t.me/axi_disscusion"}
            ],
            [
                {"text": "📲 WHATSAPP COMMUNITY", "url": "https://chat.whatsapp.com/Bh68v9KpygrGfBL6VvgRWr"}
            ]
        ]
    }

    for chat in CHAT_IDS:
        try:
            requests.post(url, data={
                "chat_id": chat,
                "text": msg,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(keyboard)
            }, timeout=10)
        except Exception as e:
            print("TG Error:", e)

# ================= COUNTRY =================

def get_country(num):
    try:
        if not str(num).startswith("+"):
            num = "+" + str(num)

        parsed = phonenumbers.parse(num, None)
        region = phonenumbers.region_code_for_number(parsed)

        if not region:
            return "Unknown", "🌍"

        country = pycountry.countries.get(alpha_2=region).name
        flag = "".join(chr(127397 + ord(c)) for c in region)

        return country, flag
    except:
        return "Unknown", "🌍"

# ================= OTP =================

def get_otp(msg):
    msg = str(msg)

    # Match: 123-456 OR 123 456
    match = re.findall(r"\b\d{3}[-\s]?\d{3}\b", msg)
    if match:
        return match[0]

    # Match normal: 4 to 6 digits
    match = re.findall(r"\d{4,6}", msg)
    return match[0] if match else "N/A"

def clean_otp(otp):
    return otp.replace("-", "").replace(" ", "")

def mask(num):
    num = str(num)
    return num[:3] + "****" + num[-3:] if len(num) > 6 else num

# ================= FORMAT =================

def make_message(rec):

    num = rec.get("number")
    msg = rec.get("message")
    service = rec.get("cli")
    time_ = rec.get("datetime")

    country, flag = get_country(num)

    raw_otp = get_otp(msg)
    otp = clean_otp(raw_otp)

    text = f"""
<b>✨ 🔐 NEW OTP RECEIVED 🔐 ✨</b>

⏰ <b>Time:</b> {time_}
🌍 <b>Country:</b> {country} {flag}
📡 <b>Service:</b> {service}
📞 <b>Number:</b> {mask(num)}

🔑 <b>OTP CODE:</b> <code>{otp}</code>

💬 <b>Message:</b>
<i>{msg}</i>

━━━━━━━━━━━━━━━━━━
🔥 <b>POWERED BY MK ASAD KHAN</b>
"""

    return text, otp

# ================= API =================

def fetch():
    try:
        r = requests.get(BASE_URL, params={
            "token": API_TOKEN,
            "fromdate": "1970-01-01 00:00:00",
            "todate": "2099-12-31 23:59:59",
            "records": 50
        }, timeout=10)

        return r.json()
    except Exception as e:
        print("API Error:", e)
        return {}

# ================= LOOP =================

def loop():
    global seen

    print("🚀 BOT RUNNING...")

    while True:
        data = fetch()

        if data.get("status") == "Success":

            for rec in data.get("data", []):

                uid = str(rec)

                if uid not in seen:
                    seen.add(uid)

                    msg, otp = make_message(rec)
                    send(msg, otp)

                    print("Sent:", rec.get("number"))

            save_seen(seen)

        time.sleep(1)

# ================= FLASK =================

app = Flask(__name__)

@app.route("/")
def home():
    return Response("Bot Running ✅", 200)

# ================= START =================

if __name__ == "__main__":
    threading.Thread(target=loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
