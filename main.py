import base64
import json
import os
import requests
from flask import Flask, jsonify, request

# --- تنظیمات اختصاصی ربات TM ---
RUBIKA_TOKEN = (
    "CEJHFF0AKOLXZQEYMZHLJIXEMEVOMVOJGZVKOYYJFPKNDTPEIZVVTNVPNZQYJVEZ"
)
GEMINI_KEY = "AQ.Ab8RN6IyHpgbGEe72KsazzPRqXXNqqpWeD01Ysm3MQCTSIw0jw"
CHANNEL_ID = "Tm_Artw0rk"

BASE_URL = f"https://botapi.rubika.ir/v01/{RUBIKA_TOKEN}/"
DB_FILE = "users_db.json"

app = Flask(__name__)


def load_db():
  if os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "r") as f:
        return json.load(f)
    except Exception:
      pass
  return {}


def save_db(db):
  with open(DB_FILE, "w") as f:
    json.dump(db, f, ensure_ascii=False, indent=2)


db = load_db()


def send_message(chat_id, text):
  try:
    url = BASE_URL + "sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload, timeout=10)
  except Exception as e:
    print(f"❌ خطا در ارسال پیام: {e}")


def get_user_level(total_xp):
  if total_xp < 200:
    return "🥉 نوآموز گرافیک"
  elif total_xp < 500:
    return "🥈 طراح جدی"
  elif total_xp < 1000:
    return "🥇 طراح حرفه‌ای"
  else:
    return "👑 استاد گرافیک (TM)"


def analyze_thumbnail_with_ai(image_bytes):
  prompt = """
    تو منتقد ارشد گرافیک در مجموعه TM هستی. شدیداً سخت‌گیرانه، دقیق و بدون تعارف کار را نقد کن.
    پاسخ را دقیقاً در قالب فرمت زیر به فارسی ارسال کن:

    🎨 نوع طراحی: Thumbnail / Graphic
    ⭐ امتیاز AI: [یک عدد بین ۱۰ تا ۱۰۰]
    ✅ نقاط قوت: [۲ مورد خلاصه با ایموجی]
    🔧 معایب و بهبود: [۲ مورد خلاصه با ایموجی]
    💬 تحلیل نهایی: [یک جمله بسیار خلاصه در مورد حس و کیفیت کار]
    💰 ارزش جایزه: [یک عدد بین ۱۰۰۰ تا ۵۰۰۰۰ فقط عدد به تومان برای کارهای با کیفیت بالا]
    """
  url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
  img_b64 = base64.b64encode(image_bytes).decode("utf-8")

  payload = {
      "contents": [{
          "parts": [
              {"text": prompt},
              {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
          ]
      }]
  }

  try:
    res = requests.post(url, json=payload, timeout=20)
    return res.json()["candidates"][0]["content"]["parts"][0]["text"]
  except Exception:
    return "❌ خطایی در پردازش هوش مصنوعی رخ داد."


@app.route("/", methods=["POST", "GET"])
def webhook():
  if request.method == "GET":
    return "TM Bot Server is Running!"

  data = request.get_json()
  if not data:
    return jsonify({"status": "ok"})

  msg = data.get("message", {}) or data.get("new_message", {})
  if not msg:
    return jsonify({"status": "ok"})

  chat_id = msg.get("chat_id") or msg.get("sender_id")
  user_id = str(chat_id)
  text = msg.get("text", "")

  if user_id not in db:
    db[user_id] = {
        "xp": 0,
        "balance": 0,
        "sub_count": 0,
    }
    save_db(db)

  user = db[user_id]

  # پاسخ به دستورات متنی
  if text in ["/start", "راهنما", "start"]:
    guide = f"""✨ **به ربات تحلیل گرافیک TM خوش آمدید!** ✨

📢 جهت استفاده، عضویت در کانال الزامی است:
👉 @{CHANNEL_ID}

🎨 **راهنما:** عکس تامنیل خود را فرستاده و کلمه **گرافیک** را بنویسید.
💳 **خرید اشتراک:** ارسال عبارت **خرید اشتراک**

🏆 **سطح شما:** {get_user_level(user['xp'])}
⭐ **مجموع امتیاز:** {user['xp']}
💰 **موجودی کیف‌‌پول:** {user['balance']:,} تومان
🎟️ **اعتبار اشتراک باقی‌مانده:** {user['sub_count']} کار"""
    send_message(chat_id, guide)

  elif text == "خرید اشتراک":
    sub_text = f"""💳 **اشتراک ویژه TM (قیمت: ۱۵۰,۰۰۰ تومان)**

🌟 **مزایا:**
دریافت جایزه نقدی (از ۱,۰۰۰ تا ۵۰,۰۰۰ تومان) به ازای ۱۰ تامنیل بعدی بر اساس خفن بودن طرح!

📌 جهت فعال‌سازی به آیدی پشتیبانی یا کانال مراجعه کنید:
👉 @{CHANNEL_ID}"""
    send_message(chat_id, sub_text)

  elif "گرافیک" in text and ("file" in msg or "photo" in msg):
    send_message(
        chat_id, "⏳ **در حال تحلیل دقیق تامنیل توسط هوش مصنوعی TM...**"
    )
    try:
      file_info = msg.get("file", {}) or msg.get("photo", {})
      file_url = file_info.get("file_url") or file_info.get("link")

      if file_url:
        file_bytes = requests.get(file_url).content
        ai_response = analyze_thumbnail_with_ai(file_bytes)

        # افزایش امتیاز
        gained_xp = 15
        user["xp"] += gained_xp

        reward_msg = ""
        if user["sub_count"] > 0:
          reward = 5000  # جایزه متغیر بر اساس ارزیابی
          user["balance"] += reward
          user["sub_count"] -= 1
          reward_msg = (
              f"\n\n🎁 **جایزه نقدی:** {reward:,} تومان اضافه شد!"
              f"\n🎟️ **اعتبار اشتراک:** {user['sub_count']} کار باقی‌مانده"
          )

        save_db(db)

        final_output = f"""📊 **نتیجه ارزیابی تخصصی TM**
━━━━━━━━━━━━━━━━━━
{ai_response}
━━━━━━━━━━━━━━━━━━
➕ **{gained_xp}+ امتیاز دریافت شد!**
🏅 **مجموع امتیاز:** {user['xp']} | **سطح:** {get_user_level(user['xp'])}{reward_msg}

📢 کانال ما: @{CHANNEL_ID}"""

        send_message(chat_id, final_output)
    except Exception:
      send_message(chat_id, "❌ خطایی در بررسی تصویر رخ داد.")

  return jsonify({"status": "ok"})


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
